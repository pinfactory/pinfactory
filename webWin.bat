@echo off

SET DATASOURCE=market@market.pinfactory.org
trap cleanup EXIT
pushd %PWD%
REM UNKNOWN: {"type":"Redirect","op":{"text":">","type":"great"},"file":{"text":"/dev/null","type":"Word"}}
cd %undefined%
docker ps
@REM REM UNKNOWN: {"type":"Redirect","op":{"text":">","type":"great"},"file":{"text":"/dev/null","type":"Word"}} || CALL :dockerfail
@REM ssh %DATASOURCE% true || echo "Can't connect to %DATASOURCE%"
@REM IF -e \usr\bin\pass && REM UNKNOWN: {"type":"Pipeline","commands":[{"type":"Command","name":{"text":"/usr/bin/pass","type":"Word"},"suffix":[{"text":"config/market","type":"Word"}]},{"type":"Command","name":{"text":"grep","type":"Word"},"suffix":[{"text":"-q","type":"Word"},{"text":"config","type":"Word"}]}]} (
@REM   COPY  src\db_dump.sql src\db_dump.bak
@REM   ssh %DATASOURCE% pg_dump --user postgres market REM UNKNOWN: {"type":"Redirect","op":{"text":">","type":"great"},"file":{"text":"src/db_dump.sql","type":"Word"}} || echo "Failed to get live data from %DATASOURCE%"
@REM )
set -x
docker build --tag=market_web .
docker run --name market_web_local -p 5000:5000 -e FLASK_APP=/srv/market/webapp.py -e FLASK_ENV=development -e TEMPLATES_AUTO_RELOAD=True -e LC_ALL=C.UTF-8 -e LANG=C.UTF-8 --volume "C:\Users\CHamge Me\Desktop\Web3\pinfactory\src":/srv/market --entrypoint=/srv/market/inside_test.sh market_web /usr/local/bin/flask run --host=0.0.0.0

EXIT /B %ERRORLEVEL%

:cleanup
mv src\db_dump.bak src\db_dump.sql
EXIT /B 0

:dockerfail
echo
echo "Docker not found. Check that Docker is installed and running."
echo "See the "Getting Started" section of README.md for more info."
echo
exit 1
EXIT /B 0	