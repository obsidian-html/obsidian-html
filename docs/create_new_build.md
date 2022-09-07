# Create new pip build
Below is a censored build script that I use to create a new version.
This page is for reference if someone wants to create their own fork or take over the project in the future.

## Steps to complete
- Update the setup.cfg with the new version string (manual)
- Update the `version` file at obsidianhtml/src/version (script)
- Remove previous builds from build folder (script)
- Create new build (script)
- Upload new build to pip (script)

## Example script
``` bash
# Config
obsidian_folder="/home/user/git/obsidian-html"

# Move to root of the git repo
cd $obsidian_folder

# get and then set version
version=$(cat setup.cfg | grep 'version =')
version="${version#*= }"
echo $version
echo "$version" > obsidianhtml/src/version

# Remove previous builds
rm -rf dist

# Create new build
python -m build
if [ $? -ne 0 ]; then
    echo "Python script failed. Exited."
    cd $origin
    exit 1
fi

rm -rf "/home/user/git/obsidian-html/build"

echo "Continue? (y/n)"
read yn
if [ "$yn" != "y" ]; then
    echo "Aborted"
    exit 0
fi

# Upload to PyPi
python -m twine upload --repository pypi dist/*
```
