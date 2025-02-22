import os
from argparse import ArgumentParser
from tempfile import mkdtemp
from git import Repo
from terraform_compliance import __app_name__, __version__
from terraform_compliance.common.readable_dir import ReadableDir
from terraform_compliance.common.readable_plan import ReadablePlan
from radish.main import main as call_radish


print('{} v{} initiated\n'.format(__app_name__, __version__))


class ArgHandling(object):
    pass


def cli(arghandling=ArgHandling(), argparser=ArgumentParser(prog=__app_name__,
                                                            description="BDD Test Framework for Hashicorp terraform")):
    args = arghandling
    parser = argparser
    parser.add_argument("--terraform", "-t", dest="terraform_file", metavar='terraform_file', type=str, nargs='?',
                        help="The absolute path to the terraform executable.", required=False)
    _, radish_arguments = parser.parse_known_args(namespace=args)

    # TODO: Create a custom usage() since it just shows -t right now

    parser.add_argument("--features", "-f", dest="features", metavar='feature directory', action=ReadableDir,
                        help="Directory (or git repository with 'git:' prefix) consists of BDD features", required=True)
    parser.add_argument("--planfile", "-p", dest="plan_file", metavar='plan_file', action=ReadablePlan,
                        help="Plan output file generated by Terraform", required=True)
    parser.add_argument("--identity", "-i", dest="ssh_key", metavar='ssh private key', type=str, nargs='?',
                        help="SSH Private key that will be use on git authentication.", required=False)
    parser.add_argument("--version", "-v", action="version", version=__version__)

    _, radish_arguments = parser.parse_known_args(namespace=args)

    steps_directory = os.path.join(os.path.split(os.path.abspath(__file__))[0], 'steps')

    # SSH Key is given for git authentication
    ssh_cmd = {}
    if args.ssh_key:
        ssh_cmd = {"GIT_SSH_COMMAND": "ssh -l {} -i {}".format('git', args.ssh_key)}

    # A remote repository used here
    if args.features.startswith(('http', 'https', 'ssh')):
        features_git_repo = args.features
        args.features = mkdtemp()

        Repo.clone_from(url=features_git_repo, to_path=args.features, env=ssh_cmd)

    features_directory = os.path.join(os.path.abspath(args.features))
    print('* Features  : {}{}'.format(features_directory,
                                     (' ({})'.format(features_git_repo) if 'features_git_repo' in locals() else '')))

    print('* Plan File : {}'.format(args.plan_file))
    commands = ['radish',
                '--write-steps-once',
                features_directory,
                '--basedir', steps_directory,
                '--user-data=plan_file={}'.format(args.plan_file)]
    commands.extend(radish_arguments)

    print('\n. Running tests.')
    result = call_radish(args=commands[1:])

    return result


if __name__ == '__main__':
    cli()
