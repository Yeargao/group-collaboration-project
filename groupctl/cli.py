import argparse
import datetime as dt
import json
import pathlib
import re
import secrets
import subprocess
import sys

ROOT = pathlib.Path.cwd()
TYPES = {'change_published','finding','question','answer','review','test_result','integration_result','blocker','final_candidate','final_result'}
COMMON = {'protocol_version','event_id','event_type','group_id','person_id','created_at','related_events'}


def git(*args, check=True):
    p = subprocess.run(['git', *args], cwd=ROOT, text=True, capture_output=True)
    if check and p.returncode:
        raise RuntimeError(f"git {' '.join(args)}: {p.stderr.strip()}")
    return p.stdout.strip()


def read(path):
    return json.loads((ROOT/path).read_text(encoding='utf-8'))


def config():
    c=read('.group/group.json')
    if not {'protocol_version','group_id','canonical_branch','assignment_file'} <= c.keys():
        raise ValueError('Invalid group configuration')
    return c


def identity():
    p=ROOT/'.group/local/identity.json'
    if not p.exists():
        raise RuntimeError('Set identity with: python -m groupctl identity PERSON_ID')
    ident=json.loads(p.read_text(encoding='utf-8'))['person_id']
    if not (ROOT/f'.group/members/{ident}.json').exists():
        raise RuntimeError('Member descriptor not found')
    return ident


def event(kind, payload):
    if kind not in TYPES: raise ValueError('Unknown event type')
    c=config(); person=identity()
    now=dt.datetime.now(dt.timezone.utc)
    eid=f'E-{now:%Y%m%dT%H%M%SZ}-{person}-{secrets.token_hex(3)}'
    obj=dict(protocol_version='0.1',event_id=eid,event_type=kind,group_id=c['group_id'],person_id=person,created_at=now.isoformat().replace('+00:00','Z'),related_events=[],**payload)
    path=ROOT/f'.group/events/{eid}.json'; path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(obj,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    return path


def events():
    found=[]
    for p in sorted((ROOT/'.group/events').glob('*.json')):
        try:
            e=json.loads(p.read_text(encoding='utf-8'))
            if COMMON <= e.keys() and e['event_type'] in TYPES: found.append(e)
        except (ValueError,KeyError): pass
    return found

def remote_events():
    """Read collaboration events from remote personal branches."""
    found = {}

    branches = git(
        'for-each-ref',
        '--format=%(refname)',
        'refs/remotes/origin/people/'
    ).splitlines()

    for branch in branches:
        paths = git(
            'ls-tree',
            '-r',
            '--name-only',
            branch,
            '--',
            '.group/events'
        ).splitlines()

        for path in paths:
            if not path.endswith('.json'):
                continue

            try:
                content = git('show', f'{branch}:{path}')
                e = json.loads(content)

                if (
                    COMMON <= e.keys()
                    and e['event_type'] in TYPES
                ):
                    found[e['event_id']] = e

            except (RuntimeError, ValueError, KeyError):
                continue

    return sorted(
        found.values(),
        key=lambda e: (e['created_at'], e['event_id'])
    )

def publish_event(path):
    git('add',str(path.relative_to(ROOT)))
    git('commit','-m',f'group event: {path.stem}')
    git('push','-u','origin',git('branch','--show-current'))


def init(args):
    base=ROOT/'.group'
    for d in ('assignment','members','events','final','local'): (base/d).mkdir(parents=True,exist_ok=True)
    (base/'local/.gitkeep').touch()
    group=base/'group.json'
    if group.exists(): raise RuntimeError('Group already initialized')
    group.write_text(json.dumps(dict(protocol_version='0.1',group_id=args.group,canonical_branch=args.canonical,assignment_file='.group/assignment/assignment.md'),indent=2)+'\n')
    (base/'assignment/assignment.md').write_text('# Group Assignment\n\nReplace with the actual group programming assignment.\n')
    print('Initialized .group/; commit these files to the canonical branch.')


def member(args):
    path=ROOT/f'.group/members/{args.person}.json'
    if path.exists(): raise RuntimeError('Member already exists')
    path.parent.mkdir(parents=True,exist_ok=True)
    obj=dict(protocol_version='0.1',person_id=args.person,display_name=args.name,joined_at=dt.datetime.now(dt.timezone.utc).isoformat())
    path.write_text(json.dumps(obj,indent=2)+'\n')
    print(f'Created {path}; commit and push the membership descriptor.')


def set_identity(args):
    if not (ROOT/f'.group/members/{args.person}.json').exists(): raise RuntimeError('Member must be registered first')
    p=ROOT/'.group/local/identity.json';p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps({'person_id':args.person})+'\n');print(f'Local identity: {args.person}')


def status(args):
    c=config(); print('Group:',c['group_id'],'Person:',identity())
    print('Branch:',git('branch','--show-current'),'Commit:',git('rev-parse','HEAD'))
    print('Uncommitted:\n'+(git('status','--short') or '(clean)'))
    git('fetch','origin',check=False)
    target=f"origin/{c['canonical_branch']}"
    if git('rev-parse','--verify',target,check=False):
        print('Canonical:',git('rev-parse',target))
        print('Behind/ahead:',git('rev-list','--left-right','--count',f'{target}...HEAD'))
    print('Events:',len(events()))
    for e in events()[-8:]: print(e['event_type'],e.get('change_id',''),e['event_id'])


def sync(args):
    print('Before sync:',git('branch','--show-current'),git('rev-parse','HEAD'))
    if git('status','--porcelain'): raise RuntimeError('Working tree not clean; protect unfinished work before sync')
    git('fetch','--all','--tags')
    print('Recent group events:')
    all_events = {
        e['event_id']: e
        for e in events()
    }

    for e in remote_events():
        all_events[e['event_id']] = e

    recent_events = sorted(
        all_events.values(),
        key=lambda e: (e['created_at'], e['event_id'])
    )

    for e in recent_events[-12:]:
        print(e['event_type'], e.get('change_id', ''), e['event_id'])
    c=config(); branch=git('branch','--show-current')
    if branch != c['canonical_branch']:
        result=git('merge','--no-edit',f"origin/{c['canonical_branch']}",check=False)
        if git('ls-files','-u'): raise RuntimeError('Merge conflicts require AI/human inspection and resolution')
        print('Canonical integration:',result or 'complete')
    print('Review incoming events and interface assumptions with your AI agent.')


def change(args):
    for e in reversed(events()):
        if e['event_type']=='change_published' and e.get('change_id')==args.change: return e
    raise RuntimeError('Change not found: '+args.change)


def inspect(args):
    e=change(args);print(json.dumps(e,indent=2,ensure_ascii=False))
    git('fetch','origin')
    print('Commit:\n',git('show','--stat','--oneline',e['commit']))
    print('Diff:\n',git('show','--format=fuller',e['commit']))


def pub(args):
    branch=git('branch','--show-current')
    if not re.fullmatch(r'people/[^/]+/.+',branch): raise RuntimeError('PUB requires a personal work branch')
    if git('status','--porcelain'): raise RuntimeError('Commit and inspect local work before publishing')
    git('push','-u','origin',branch)
    commit=git('rev-parse','HEAD')
    cid='C-'+secrets.token_hex(4)
    changed=git('diff-tree','--no-commit-id','--name-only','-r',commit).splitlines()
    path=event('change_published',dict(change_id=cid,branch=branch,commit=commit,summary=args.summary,files_changed=changed,interface_changes=args.interface or [],tests_run=args.test or [],known_issues=args.issue or [],proposed_for_integration=True))
    publish_event(path);print('Published:',cid)


def record(args):
    payload=json.loads(pathlib.Path(args.json).read_text(encoding='utf-8'))
    if not isinstance(payload,dict) or COMMON & payload.keys(): raise ValueError('Payload must be an object without common envelope fields')
    path=event(args.kind,payload)
    if args.push: publish_event(path)
    print(path)


def integrate(args):
    e=change(args)
    git('fetch','origin')
    print('Integrating',args.change,'from',e['branch'],e['commit'])
    if git('status','--porcelain'): raise RuntimeError('Working tree must be clean')
    if not git('cat-file','-e',e['commit'],check=False)=='':
        raise RuntimeError('Referenced commit not available locally')
    print('Inspect change before integration with: python -m groupctl inspect',args.change)
    result=git('merge','--no-ff','--no-edit',e['commit'],check=False)
    if git('ls-files','-u'):
        print('Conflict files:\n',git('diff','--name-only','--diff-filter=U'))
        raise RuntimeError('Conflict: AI/human must inspect both intents and resolve, then verify and record integration_result')
    if not git('merge-base','--is-ancestor',e['commit'],'HEAD',check=False)=='':
        raise RuntimeError('Commit incorporation not verified')
    print(result or 'Merged')
    print('Run build/tests and semantic review, then publish integration_result via record.')


def main():
    p=argparse.ArgumentParser(prog='groupctl');sub=p.add_subparsers(dest='cmd',required=True)
    s=sub.add_parser('init');s.add_argument('--group',required=True);s.add_argument('--canonical',default='main');s.set_defaults(func=init)
    s=sub.add_parser('member');s.add_argument('person');s.add_argument('name');s.set_defaults(func=member)
    s=sub.add_parser('identity');s.add_argument('person');s.set_defaults(func=set_identity)
    for name,fn in [('status',status),('sync',sync)]:sub.add_parser(name).set_defaults(func=fn)
    s=sub.add_parser('inspect');s.add_argument('change');s.set_defaults(func=inspect)
    s=sub.add_parser('integrate');s.add_argument('change');s.set_defaults(func=integrate)
    s=sub.add_parser('pub');s.add_argument('--summary',required=True);s.add_argument('--interface',action='append');s.add_argument('--test',action='append');s.add_argument('--issue',action='append');s.set_defaults(func=pub)
    s=sub.add_parser('record');s.add_argument('kind',choices=sorted(TYPES));s.add_argument('json');s.add_argument('--push',action='store_true');s.set_defaults(func=record)
    a=p.parse_args()
    try:a.func(a)
    except (RuntimeError,ValueError,subprocess.CalledProcessError) as exc: print('ERROR:',exc,file=sys.stderr);sys.exit(1)

if __name__=='__main__':main()
