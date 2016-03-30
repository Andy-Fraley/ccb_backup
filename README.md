# ccb_backup
Data retrieval and backup utilities for Church Community Builder (CCB)

###What is Church Community Builder?

[Church Community Builder](https://churchcommunitybuilder.com/) is SaaS for running a church.  The software is able to track church membership, groups within the church including small groups and committees, events including worship service and group meetings along with attendance to those events, and also pledges and giving.  So it's pretty broad and over time ends up containing a lot of key information to the church.

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
