# ccb_backup
Backup utilities for Church Community Builder (CCB)

STATUS
2016-01-22 Third utility, get_contributions.py, is working.
2016-01-22 Second utility, get_individuals.py, is working.
2016-01-22 Initial utility, get_pledges.py, is working.
2016-01-20 These are under development (non-working state) for now.

TODOS
- get_attendance.py (can base on earlier ccb_api_dump_attendance_v2.py utility)
- get_groups.py
- ccb_backup.py (call get_pledges.py, get_individuals.py, etc. then take all results and ZIP them up
  into posted backup file into S3)
- Make "start date" setable across all utilities (where present)

