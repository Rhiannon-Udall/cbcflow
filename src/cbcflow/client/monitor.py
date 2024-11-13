"""Methods for setting up and running monitors"""
import argparse
import os
from shutil import which

from glue import pipeline
from crontab import CronTab

from ..core.utils import setup_logger
from ..core.database import LocalLibraryDatabase

logger = setup_logger(name=__name__)


def get_base_parser():
    """Generate the standard monitor parser"""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "library",
        help="The library which the monitor will update",
    )
    parser.add_argument(
        "--monitor-interval",
        type=int,
        default=2,
        help="The interval in hours between runs of the monitoring job",
    )
    parser.add_argument(
        "--rundir",
        default=None,
        help="The directory in which to produce sub and output files",
    )
    parser.add_argument(
        "--monitor-minute",
        type=int,
        default=0,
        help="If passed, sets the minute to run the job, so that one can get quick feedback"
        "Defaults to 0 for normal operation",
    )
    return parser


def generate_crontab() -> None:
    """Setup a crontab to run the monitor on an interval"""
    parser = get_base_parser()
    parser.add_argument(
        "--user-name",
        default=os.environ.get("USER", "N/A"),
        help="The LIGO accounting user for the job to be tagged with",
    )

    args = parser.parse_args()

    if args.rundir is None:
        rundir = os.getcwd()
    else:
        rundir = args.rundir

    monitor_exe = which("cbcflow_monitor_run")
    monitor_args = f" {os.path.expanduser(args.library)} "

    log_file = f"{rundir}/monitor.log"

    cron = CronTab(user=args.user_name)
    job = cron.new(command=f"{monitor_exe} {monitor_args} >> {log_file} 2>&1")
    job.hour.every(args.monitor_interval)
    job.minute.on(args.monitor_minute)
    cron.write()


def generate_crondor() -> None:
    """Creates a periodic condor to run the monitor action."""

    parser = get_base_parser()
    parser.add_argument(
        "--ligo-accounting",
        default=os.environ.get("LIGO_ACCOUNTING", "N/A"),
        help="The LIGO accounting group for the job to be tagged with",
    )
    parser.add_argument(
        "--ligo-user-name",
        default=os.environ.get("LIGO_USER_NAME", "N/A"),
        help="The LIGO accounting user for the job to be tagged with",
    )
    args = parser.parse_args()

    if args.rundir is None:
        rundir = os.getcwd()
    else:
        rundir = args.rundir

    monitor_exe = which("cbcflow_monitor_run")
    monitor_job = pipeline.CondorJob(
        universe="vanilla", executable=monitor_exe, queue=1
    )
    monitor_job.set_log_file(os.path.join(rundir, "monitor.log"))
    monitor_job.set_stdout_file(os.path.join(rundir, "monitor.out"))
    monitor_job.set_stderr_file(os.path.join(rundir, "monitor.err"))
    monitor_job.add_condor_cmd("accounting_group", args.ligo_accounting)
    monitor_job.add_condor_cmd("accounting_group_user", args.ligo_user_name)
    monitor_job.add_condor_cmd("request_memory", "200 Mb")
    monitor_job.add_condor_cmd("request_disk", "10 Mb")
    monitor_job.add_condor_cmd("notification", "never")
    monitor_job.add_condor_cmd("initialdir", rundir)
    monitor_job.add_condor_cmd("get_env", "True")
    monitor_job.add_condor_cmd("on_exit_remove", "False")
    # These are the unusual settings - this makes the job repeat every N hours, at the Mth minute
    monitor_job.add_condor_cmd("cron_minute", f"{args.monitor_minute}")
    monitor_job.add_condor_cmd("cron_hour", f"* / {args.monitor_interval}")
    # This tells the job to queue 5 minutes before it's execution time, so it will be ready when the time comes
    monitor_job.add_condor_cmd("cron_prep_time", "300")
    monitor_args = f" {os.path.expanduser(args.library)} "
    monitor_job.add_arg(monitor_args)
    sub_path = os.path.join(rundir, "monitor.sub")
    monitor_job.set_sub_file(sub_path)
    monitor_job.write_sub_file()

    os.system(f"condor_submit {sub_path}")


def run_monitor() -> None:
    """
    Pulls all superevents created within the past 30 days, creates metadata if necessary,
    then pushes back any changes made in this process
    """
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "library",
        type=str,
        help="The path to the library to operate on",
    )
    parser.add_argument(
        "--branch-name",
        type=str,
        default="main",
        help="The branch the monitor should write to - defaults to main",
    )
    args = parser.parse_args()

    local_library = LocalLibraryDatabase(library_path=args.library)
    logger.info("CBCFlow monitor is beginning sweep")
    logger.info("Attempting to pull from remote")
    # Pull before we potentially checkout a new branch
    local_library.git_pull_from_remote(automated=True)
    # Make sure we switch to main for monitor operations
    local_library.git_checkout_new_branch(branch_name=args.branch_name)
    # Pull again in case the remote already existed and we want to update it
    if local_library.remote_has_merge_conflict:
        logger.info(
            "Could not pull from remote, continuing with standard sync sequence\n\
                    Before these changes can be propagated to the remote, this merge conflict\n\
                    must be resolved manually."
        )
    local_library.initialize_parent()
    # Note that we explicitly sync to main instead of any other branch
    local_library.library_parent.sync_library(branch_name=args.branch_name)
    logger.info("Updating index file for library")
    # For now we don't want to do any labelling locally, instead doing it all in gitlab
    # set_working_index... will change LastUpdate and add events
    # but won't touch the labels
    local_library.set_working_index_with_updates_to_file_index()
    local_library.write_index_file(branch_name=args.branch_name)
    local_library.git_pull_from_remote(automated=True)
    if not local_library.remote_has_merge_conflict:
        logger.info("Pushing to remote")
        local_library.git_push_to_remote()
    logger.info("Sweep completed, resting")
