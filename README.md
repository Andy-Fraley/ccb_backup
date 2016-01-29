# ccb_backup
Backup utilities for Church Community Builder (CCB)

STATUS
2016-01-29 Fourth utility, get_groups.py, is working.
2016-01-22 Third utility, get_contributions.py, is working.
2016-01-22 Second utility, get_individuals.py, is working.
2016-01-22 Initial utility, get_pledges.py, is working.
2016-01-20 These are under development (non-working state) for now.

TODOS
- get_attendance.py (can base on earlier ccb_api_dump_attendance_v2.py utility and event_profile API call)
- ccb_backup.py (call get_pledges.py, get_individuals.py, etc. then take all results and ZIP them up
  into posted backup file into S3)
- Make "start date" setable across all utilities (where present)
- Allow "start date" and "end date" across all utilities (to allow for incremental backups)?  Would only affect
  time-based things (not things like individuals, groups)
- Move from settings class to INI file approach
- Make user/pass settable on command-line or via INI file
- Make ccb-subdomain settable in INI file