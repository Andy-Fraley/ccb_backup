# ccb_backup
Data retrieval and backup utilities for Church Community Builder (CCB)

### What is Church Community Builder?

[Church Community Builder](https://churchcommunitybuilder.com/) is SaaS for running a church.  The software is able to track church membership, groups within the church including small groups and committees, events including worship service and group meetings along with attendance to those events, and also pledges and giving.  So it's pretty broad in its functionality and ends up containing a lot of key information for churches using it.

### Why were these ccb_backup (including data export) facilities created?

However, there's two key areas where CCB could stand to have more/better functionality:

1. Ability to do truly ad hoc custom reports (the built-in reports in CCB are limited and so is CCB's ability to create custom reports)
2. Ability to easily export ALL data in order to do an outside-of-CCB backup of the church's data that is stored in CCB

To work around these two issues, we've built a set of backup and data export tools for CCB that we use for both purposes.  They allow you to extract CSV data sets for:
* Individuals (**get_individuals.py**. _NOTE - "People", not "Individuals" is the CCB object name_)
* Groups (**get_groups.py**)
* Attendance & Events (**get_attendance.py**)
* Pledges (**get_pledges.py**)
* Contributions (**get_contributions.py**)

We use these data retrieval utilities to pull CSV files which we then load into Excel to do custom reporting.

For example, to pull a flat list of all People (individuals) in your CCB account, just run:
```
python get_individuals.py
```

On top of these data retrieval utilities, there's a backup utility, **ccb_backup.py**, which uses the data retrieval utilities listed above to export all of the data as a series of CSV files and then ZIP's them up (encrypted) and can even push the passworded backup ZIP file to Amazon Web Services (AWS) S3.  The backup utility can be set up on cron and configured to do things like keep a daily backup for 7 days, keep a weekly backup for 5 weeks, and keep a monthly backup forever (which is how we have ours configured).

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
