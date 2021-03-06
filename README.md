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

For those intending to use **ccb_backup.py** to do daily/weekly/monthly backups automatically using cron, here's a sample crontab entry as an example:
```
30 2 * * * /usr/bin/python /home/ccb_backup/src/ccb_backup/ccb_backup.py --post-to-s3 --delete-zip --notification-emails name@email_domain.com > /dev/null 2>&1
```

"30 2 * * *" indicates to run nightly at 2:30am.  The **--post-to-s3** and **--delete-zip** flags cause **ccb_backup.py** to post the created ZIP file to AWS S3 and then delete it.  The **--notification-emails name@email_domain.com** causes an email to be sent that confirms successful backup completion or reports backup errors.  And **"> /dev/null 2>&1"** simply causes stdout and stderr output to be ignored.  You'll need to adjust **/usr/bin/python** to be the location of your Python 2.x executable.  And you'll need to adjust **/home/ccb_backup/src/ccb_backup/ccb_backup.py** to be the location of where you've installed the **ccb_backup** utilities.

### How to install and configure the ccb_backup utility set

The **ccb_backup** utilities are written in Python (2.x). They should run cross-platform but have only been tested on MacOS, Ubuntu, and CentOS. Prerequisites include:
* MacOS, Ubuntu, or CentOS (if you want to run on Windows or other 'nix platforms, may work...will try and support you)
* Python 2.x
* Python packages: requests, boto3, pytz

You can install these **ccb_backup** utilities, just by cloning this git repo or using GitHub's "Download ZIP" button and unzipping the files.  Once installed, you need to create your own **ccb_backup.ini** file by copying and editing the **ccb_backup__sample.ini** file included in this **ccb_backup** repo.

Here's some quick guidance on entries required in the **ccb_backup.ini** file.
```
[logging]
level=Info
```

The 'level' flag in the '[logging]' section can be set to **Info** (default), **Warning**, or **Error**.  All messages higher than or equal to specified precedence level are output to stdout and message.log file.

```
[ccb]
app_username=
app_password=
api_username=
api_password=
```

These are CCB logins.  **app_username** and **api_username** are typically email addresses.  The reason **_BOTH_** app and API usernames are needed is because unfortunately, CCB does not expose all of their data via API.  Therefore, when the data is not retrievable using the API, it is retrieved with a bit of web screen scraping from CCB app itself. (CCB - please improve your API with an API-first approach so that all data is gettable/settable via your API.) The app login must have privilege to read all information retrieved (INDIVIDUALS, GROUPS, ATTENDANCE, EVENTS, CONTRIBUTIONS, PLEDGES).  The API login must have privilege to read the same.

```
[ccb]
subdomain=
```

This is your church's subdomain on CCB. If you login to CCB at **mychurch**.ccbchurch.com, then it is **mychurch**.

```
[zip_file]
password=
```

This is the password you want to use to encrypt ZIP files created by the **ccb_backup.py** utility.

```
[aws]
access_key_id=
secret_access_key=
region_name=
s3_bucket_name=
```

These are your AWS S3 credentials. The **access_key_id** and **secret_access_key** should correspond to an IAM user that has been granted the following privileges on an S3 bucket you create: **s3:DeleteObject**, **s3:GetObject**, **s3:PutObject**, and **s3:ListBucket**.  Below is a sample AWS S3 bucket policy for a created IAM user 'ccb_backup' (bucket policies are settable under "Properties" on a bucket in the AWS S3 console).

```
{
	"Version": "2012-10-17",
	"Id": "Policy1111111111111",
	"Statement": [
		{
			"Sid": "Stmt1111111111111",
			"Effect": "Allow",
			"Principal": {
				"AWS": "arn:aws:iam::9999999999:user/ccb_backup"
			},
			"Action": [
				"s3:DeleteObject",
				"s3:GetObject",
				"s3:PutObject"
			],
			"Resource": "arn:aws:s3:::my-ccb-backups-bucketname/*"
		},
		{
			"Sid": "Stmt2222222222222",
			"Effect": "Allow",
			"Principal": {
				"AWS": "arn:aws:iam::9999999999:user/ccb_backup"
			},
			"Action": "s3:ListBucket",
			"Resource": "arn:aws:s3:::my-ccb-backups-bucketname"
		}
	]
}
```

Also in your **ccb_backup.ini** file you'll need to configure your backup schedule.  A reasonable one is provided by default:
```
[schedules]
schedule1=daily,1d,7
schedule2=weekly,1w,5
schedule3=monthly,1M,0
```

The **daily**, **weekly**, and **monthly** names must directly correspond to 'daily', 'weekly', and 'monthly' folders that you must create within the S3 bucketname you specified before running **ccb_backup.py** against S3.

The schedule above tells **ccb_backup.py** to post the created ZIP file to the 'daily' folder in the specified S3 bucket if it is more than one day (1d) newer than the most recent backup and delete the oldest backup(s) in that folder if more than 7 exist.  Similarly, it tells **ccb_backup.py** to post the created ZIP file to the 'weekly' folder if more than one week (1w) newer and maintain 5 weekly backups.  And post to 'monthly' if one month (1M) newer than most recent and allow for an infinite (by specifying to keep '0' backup instances in the 'monthly' folder) number of monthly backups. Extending this, you can see how you could keep 'monthly' backups for a year (keep 12) and then keep 'yearly' backups forever, for example.

Finally, you can configure the Gmail box that **ccb_backup.py** will send from:
```
[notification_emails]
gmail_user=my_gmail_address@gmail.com
gmail_password=my-password
```

Note that depending how you've configured Gmail security (if 2-step authentication is on, for example), you may need to create a Gmail app password and specify it above.

### Your help

If you have recommended bugfixes or enhancements, please send a pull request.

# Change Log

* 2016-03-31 Initial public release
