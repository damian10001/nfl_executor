# nfl_executor
# Script for automation running NFL (and not only) testcases


Requirements:
-	View is needed and config spec set to desired branch/label
-	Setup is sourced
-	Diameter Daemon must be running

What script can do?
-	Generate makefile
-	Compile NFL module
-	Generate database and add testcases to execution
-	Generate config files (script has own config, so tiger config is untouched)
-	Install build
-	Run initial configuration
-	Run testcases and rerun failed (turbo mode is turned on, repeat is set to 3)
-	Logs are stored in: /home/<signum>/logs/NFL/<date>_<time>

Planned features in future:
-	Check if build is installed correctly, if not then will try install again - DONE
-	Check verdict of initial configuration
-	Automatic select latest build from Jenkins
-	Possibility to run other modules than NFL - DONE
-	Send mail when regression is done (thanks Marcin for suggestion)

