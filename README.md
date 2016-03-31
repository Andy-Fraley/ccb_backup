# ccb_backup
Data retrieval and backup utilities for Church Community Builder (CCB)

### What is Church Community Builder?

[Church Community Builder](https://churchcommunitybuilder.com/) is SaaS for running a church.  The software is able to track church membership, groups within the church including small groups and committees, events including worship service and group meetings along with attendance to those events, and also pledges and giving.  So it's pretty broad in its functionality and ends up containing a lot of key information for churches using it.

### Why were these ccb_backup (including data export) facilities created?

However, there's two areas where CCB could stand to have more/better functionality:
1. Ability to do truly ad hoc custom reports (the built-in reports in CCB are limited and so is CCB's ability to create custom reports)
2. Ability to easily export ALL data in order to do an outside-of-CCB backup of the church's data that is stored in CCB

To work around these two issues, we've built a set of backup and data export tools for CCB that we use for both purposes.  They allow you to extract CSV data sets for:
* Individuals (**get_attendance.py**. _NOTE - "People", not "Individuals" is the CCB object name_)
* Groups (**get_groups.py**)
* Attendance & Events (**get_attendance.py**)
* Pledges (**get_pledges.py**)
* Contributions (**get_contributions.py**)

They're written in Python (2.x).

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
