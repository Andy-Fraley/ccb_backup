# ccb_backup
Data retrieval and backup utilities for Church Community Builder (CCB)

### What is Church Community Builder?

[Church Community Builder](https://churchcommunitybuilder.com/) is SaaS for running a church.  The software is able to track church membership, groups within the church including small groups and committees, events including worship service and group meetings along with attendance to those events, and also pledges and giving.  So it's pretty broad in its functionality and ends up containing a lot of key information for churches using it.

### Why were these ccb_backup (and data retrieval) utilities created?

There's two key areas where CCB could stand to have more/better functionality:

1. Ability to do truly ad hoc custom reports (the built-in reports in CCB are limited and so is CCB's ability to create custom reports)
2. Ability to easily export data stored in CCB in order to do an outside-of-CCB backup of the church's data

To work around these two issues, we've built a set of backup and data export tools for CCB that we use for both purposes.

### get_XXX.py data retrieval utilities

The **get_XXX.py** data retrieval utilties allow you to extract CSV data sets from CCB for:
* Individuals (**get_individuals.py**. _NOTE - "People", not "Individuals" is the CCB object name_)
* Groups & Participants (**get_groups.py**)
* Attendance & Events (**get_attendance.py**)
* Pledges (**get_pledges.py**)
* Contributions (**get_contributions.py**)

We use these data retrieval utilities to pull CSV files which we then load into Excel to do custom reporting.

For example, to pull a flat list of all People (individuals) in your CCB account, just run:
```
python get_individuals.py
```

By default, **get_individuals.py**, and all get_XXX.py data retrieval utilities will default the output file to a file named ./tmp/individuals_YYYYMMDDHHMMSS.csv (and will expect a ./tmp subdirectory to exist).  If you want the output file to be foobar.csv instead, just specify the output file on the command-line as follows:
```
python get_individuals.py --output-filename foobar.csv
```

All of the utilities allow you to specify output filename(s). (_NOTE: **get_groups.py** outputs two CSVs for groups and participants and **get_attendance.py** outputs two CSVs for attendance and events._) But some of the utilities allow you to control other aspects of data retrieval, for example **get_attendance.py** retrieves attendance data by default for only current year (because attendance data retrieval takes a long time), but you can specify an **--all-time** flag to allow you to pull all attendance data for all events in the system, including all of your worship services. To see all of the command-line options available for any of the **get_XXX.py** data retrieval utilities, just run:
```
python get_XXX.py --help
```

### ccb_backup.py utility

On top of these data retrieval utilities, there's a backup utility, **ccb_backup.py**, which uses the data retrieval utilities listed above to export all of the data as a series of CSV files and then ZIPs them up (encrypted with password) and can even push the passworded backup ZIP file to Amazon Web Services (AWS) S3.  The backup utility can be set up on cron and configured to do things like keep a daily backup for 7 days, keep a weekly backup for 5 weeks, and keep a monthly backup forever (which is how we have ours configured).

Running
```
python ccb_backup.py --help
```
will show many options for the **ccb_backup.py** utility.  But here's a quick summary of the most important options.

```
  --show-backups-to-do  If specified, the ONLY thing that is done is backup
                        posts and deletions to S3 are calculated and displayed
```

Usually, AWS S3 is used to store backups.  And there's buckets in S3 for 'daily', 'weekly', and 'monthly' (by default) backups.  Running **ccb_backup.py** with this flag reads from S3 and determines if there are any new backups to do and if so, prints them out.  Else, does nothing.

```
  --post-to-s3          If specified, then the created zip file is posted to
                        Amazon AWS S3 bucket (using bucket URL and password in
                        ccb_backup.ini file)
```

If **--post-to-s3** is specified, then the created ZIP file is posted to AWS S3. By default, when this is not specified, only a local ZIP file is created with backup data.

```
  --delete-zip          If specified, then the created zip file is deleted
                        after posting to S3
```

Rather than letting lots of backup ZIP files accumulate on the server where **ccb_backup.py** is run to do backups and push to S3, specifying this flag will delete the local ZIP file after it's pushed to AWS S3.

```
  --all-time            Normally, attendance data is only archived for current
                        year (figuring earlier backups covered earlier years).
                        But specifying this flag, collects attendance data not
                        just for this year but across all years
```

This flag specifies to **get_attendance.py** that it is to collect attendance data for all time (instead of just this year which is default).

```
  --backup-data-sets [BACKUP_DATA_SETS [BACKUP_DATA_SETS ...]]
                        If unspecified, *all* CCB data is backed up. If
                        specified then one or more of the following data sets
                        must be specified and only the specified data sets are
                        backed up: ATTENDANCE INDIVIDUALS CONTRIBUTIONS
                        PLEDGES GROUPS
```

Normally, all data (ATTENDANCE & Events, INDIVIDUALS, CONTRIBUTIONS, PLEDGES, and GROUPS & Participants) is backed up to a zip file.  However, it's possible using this flag to pull some of the data sets into one backup file and some into another.  For example, many churches tightly restrict who can see CONTRIBUTIONS and PLEDGES data and it's possible to push just that backup data to one backup location visible by a very limited set of people and push the rest of backup data to a more broadly visible location.

All of these utilities are written in Python (2.x). They should run cross-platform but have only been tested on MacOS, Ubuntu, and CentOS.

### How to install and configure the ccb_backup utility set

#Xxx

STATUS
- 2016-01-31 All utilities moved to ccb_backup.ini file for username/password and other key configuration settings.
- 2016-01-29 Fifth utility, get_attendance.py, is working.
- 2016-01-29 Fourth utility, get_groups.py, is working.
- 2016-01-22 Third utility, get_contributions.py, is working.
- 2016-01-22 Second utility, get_individuals.py, is working.
- 2016-01-22 Initial utility, get_pledges.py, is working.
- 2016-01-20 These are under development (non-working state) for now.

TODOS
- Write ccb_backup.py (call get_pledges.py, get_individuals.py, etc. then take all results and ZIP them up
  into posted backup file into S3)
