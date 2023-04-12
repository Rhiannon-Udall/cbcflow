"""Methods for setting up and running monitors through htcondor"""
import argparse
import logging
import os
from shutil import which

from glue import pipeline

from .configuration import get_cbcflow_config
from .database import LocalLibraryDatabase

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def generate_crondor() -> None:
    """Creates a periodic condor to run the monitor action."""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--config-file",
        default="~/.cbcflow.cfg",
        help="The cfg from which to obtain monitor configuration info",
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
        "--ligo-accounting",
        default=os.environ["LIGO_ACCOUNTING"],
        help="The LIGO accounting group for the job to be tagged with",
    )
    parser.add_argument(
        "--ligo-user-name",
        default=os.environ["LIGO_USER_NAME"],
        help="The LIGO accounting user for the job to be tagged with",
    )
    parser.add_argument(
        "--monitor-minute",
        type=int,
        default=0,
        help="If passed, sets the minute to run the job, so that one can get quick feedback"
        "Defaults to 0 for normal operation",
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
    monitor_args = f" {os.path.expanduser(args.config_file)} "
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
        "cbcflowconfig",
        type=str,
        help="The .cbcflow.cfg file to use for library and service URL info",
    )
    args = parser.parse_args()

    config_values = get_cbcflow_config(args.cbcflowconfig)
    local_library = LocalLibraryDatabase(library_path=config_values["library"])
    logger.info("CBCFlow monitor is beginning sweep")
    logger.info("Attempting to pull from remote")
    local_library.git_pull_from_remote()
    if local_library.remote_has_merge_conflict:
        logger.info(
            "Could not pull from remote, continuing with standard sync sequence\n\
                    Before these changes can be propagated to the remote, this merge conflict\n\
                    must be resolved manually."
        )
    logger.info(f"Config values are {config_values}")
    local_library.initialize_parent(source_path=config_values["gracedb_service_url"])
    local_library.library_parent.sync_library()
    logger.info("Updating index file for library")
    # In the future labelling can happen via monitor, but for now do it in gitlab
    local_library.label_index_file()
    local_library.write_index_file()
    if not local_library.remote_has_merge_conflict:
        logger.info("Pushing to remote")
        local_library.git_push_to_remote()
    logger.info("Sweep completed, resting")
