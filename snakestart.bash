#! /usr/bin/env bash

if [ -z "$1" ] ; then
	echo "A project name is required as an argument." >&2
	exit 1
fi

templatedir="$XDG_CONFIG_HOME/snakestart/template"

DATE="$(date +%Y-%m-%d)"
projectdir="${1}_${DATE}"
projectname="$(basename $1)"


cp -r "${templatedir}" "${projectdir}" && cd "${projectdir}"

find . -type f \
-exec sed -i "s/<PROJECTNAME>/${projectname}/g" {} \; \
-exec sed -i "s/<DATE>/${DATE}/g" {} \; \
-exec sed -i "s/<PROJECTDIR>/${projectdir}/g" {} \;

conda env create --file environment.yml 

exit