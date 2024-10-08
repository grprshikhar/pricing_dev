# Pricing Wizard

## Table of Contents

- [Pricing Wizard](#pricing-wizard)
  * [Table of Contents](#table-of-contents)
  * [Introduction](#introduction)
  * [Systems](#systems)
    + [Mac OSX](#mac-osx)
    + [Windows](#windows)
  * [Usage](#usage)
    + [Special note for Windows](#special-note-for-windows)
    + [User Data](#user-data)
    + [Logging](#logging)
    + [Reprice SKUs](#reprice-skus)
    + [Price new SKUs](#price-new-skus)
    + [Run report](#run-report)
    + [Suggest price review SKUs](#suggest-price-review-skus)
    + [Review Pricing Wizard data](#review-pricing-wizard-data)
  * [Unit Tests](#unit-tests)
  * [Tutorial For Setup](#tutorial-for-setup)
    + [First Time Usage](#first-time-usage)
    + [Updating Repository](#updating-repository)
    + [Setting Up An Alias/Shortcut](#alias)


## Introduction

This tool is attempting to standardise the checks we need to apply before prices go live on the Grover website.
It is important that as we scale up, we have tools which can manage increasing the numbers of SKU in a consistent manner.
We currently will still make use of Google Sheets but will start to implement checks and streamline the upload processes.

[Miro board](https://miro.com/app/board/uXjVOyEXe5Y=/?share_link_id=557505320610)

## Systems

The hope is that with the aid of Google Drive, we will not need to have a central location (ie AWS) to use this tool, but instead it can be used locally by any pricing analyst using a device which complies with Grover security requirements (eg encrypted, VPN access, centrally managed).

### Mac OSX

This tool has been developed on OSX and should therefore not require much work from the user to get it running.

 - python3
   - Install using [homebrew](https://brew.sh/)
   - `brew install python3` and follow the finalisation instructions `eval "$(/opt/homebrew/bin/brew shellenv)"`
     - You may need to check you have the terminal profile. If you do not, do `touch ~/.bash_profile` or equivalent for zsh and copy the command again.
   - Install requirements using `pip3 install -r requirements.txt`
     - If you get a message to update pip3, please follow the instructions.

### Windows

This is where things might be bumpy at first. The best working solution is to use [Windows subsystem for Linux](https://docs.microsoft.com/en-us/windows/wsl/install) which is available for Windows 10/11. This is a Microsoft supported system which allows a Linux installation to be made within the Windows environment. Further information regarding setup can be found in [this article](https://pbpython.com/wsl-python.html).

Moving forwards, the most sensible Linux OS to choose is `Ubuntu 22` which is the latest release and available on the [Microsoft Store](https://apps.microsoft.com/store/detail/ubuntu-2204-lts/9PN20MSR04DW?hl=en-us&gl=US). Some information regarding setting up `python3` is available in [this article](https://linuxize.com/post/how-to-install-python-3-9-on-ubuntu-20-04/) specifically written for `Ubuntu 20` but should be equally applicable to `Ubuntu 22.04` as can be seen in [this article](https://www.linuxcapable.com/how-to-install-python-3-9-on-ubuntu-22-04-lts/#Install_Python_39_-_PPA_Method). 

A brief summary is:
 - `sudo apt-get update`
   - This will update the package manager.
 - `sudo apt-get upgrade`
   - This will update the package manager.

Check if your Ubuntu installation contains a recent python3 version 

 - `python3 --version`

If this says `Python 3.9.X` or greater, then you just need to ensure the python package manager is available:

 - `sudo apt install python3-pip`

  Need to be in the folder with pricing wizard
  
 - `pip3 install -r requirements.txt`

And you should be ready to go!

If the python3 is older (or not installed), follow these additional commands

 - `sudo apt install software-properties-common`
   - This will install requirements for python3.9
 - `sudo add-apt-repository ppa:deadsnakes/ppa`
   - This will add the repository which contains modern python3.X releases
 - `sudo apt-get install python3.9`
   - This will ask the package manager to install python3.9.
 - `sudo apt install python3-pip`
   - This will install `pip3` for python package management
 - `pip3 install -r requirements.txt`
   - This should be the same as the OSX instructions to install the required modules.
   - If you get a message to update pip3, please follow the instructions.

## Note on numpy
If you hit an error on installation versions it is because pandas needs numpy 1.20+ but cannot work with numpy 2.X so use 1.23 to fix this

pip install numpy==1.23


## Usage

This tool is written for `python3` and makes use of standard data manipulation libraries (such as `pandas`).
The tool has the ability to access the data stored in Google Sheets and Google Drive which are shared with `Grover`.
The tool expects active user input to direct the workflow and verify any warnings. In some cases, there will be errors which have been identified which will require pricing analyst intervention but the aim is to limit these to the cases where there are issues with the chosen price points.

```
python3 pricing_wizard.py
```
This will start the tool and provide a list of options:

1) Reprice SKUs
2) Price new SKUs
3) Run report
4) Suggest price review SKUs
5) Review Pricing Wizard data
6) Exit

### Special note for Windows

When you run the WSL terminal shell, you may find that it places you in an unknown folder. In this case you need to navigate to the area where you have pricing_wizard.
This will look something like this:
```
cd /mnt/Users/<username>/<path_to_pricing_wizard>
```
If you are lost, navigate to the mount folder `cd /mnt/` and then list the folder `ls -l` this should show you the `Users` folder. You can then `cd Users` and use the list command to identify the folder which corresponds to your user area on your C drive. 


### User Data

Pricing Wizard will need to know your `redshift` username and your `admin panel` username. You can either enter these when the program is running, or you can edit the `user_data.json` file and edit the fields for your user. If these are filled in, you will only be asked for your passwords when running. These are not stored in any file when they are entered for security.

### Logging

Currently, Pricing Wizard will write out a local log file only (`pricing_wizard.log`). We will work on a method for updating a central log file in the future in case we need to check when a particular update was made and whether there were any warning which were overlooked or whether we can improve the checks/warnings/errors in the future.

### Reprice SKUs

This is likely to be the main use case. The tool will access the sheet stored in `user_data.json` but offers the change to amend this information or use a different sheet ID for a single instance. A number of checks will be run and this information will be printed to the terminal to see what was checked. In some cases there will be checks which are optional such as:

1) Checking against historical data to avoid discounting in a manner which does not comply with EU directives. This requires RedShift access.
2) Checking against RRP%. In some cases, we may not want to prevent uploads due to low pricing to encourage stock movement.
3) Summaries of the data can be provided such as showing the types of markets and rental plans, showing statistics relating to pricing and showing the final tabulated data.

The tool will download the template file from Google Drive, copy data into this and is able to save the sheet locally and upload to Google Drive using a structure of `DATE_NAME_DESCRIPTION.xlsx`.

### Price new SKUs

This function expects the pricing analyst to have a list of SKUs which the category manager has already placed into the gross margin sheet. The aim here is to run the checks on price points, RRP% and gross margin% without needing to run through multiple steps to check on the GM sheet and handle uploads. The tool will check whether the items are bulky, mark them as `new` and run through the validation checks implemented for repricing as well. The tool will use the same uploading functions as the reprice functionality.

### Run report

This is a work-in-progress.
The aim is to collate reports made by pricing analysts and set them up with a consistent interface to hook into the Pricing Wizard. This would then allow anyone to rerun a python based report. The use case is likely to be reports requiring RedShift access but can also make use of the Google Sheet and Google Drive functions.

### Suggest price review SKUs

This is a work-in-progress.
The aim here would be to process data from RedShift for specified categories and check things such as SoH, MoS, number of orders etc to identify SKUs which might need a price reduction to encourage demand, identify discounts which should be removed or even suggest increasing prices to cope with demand. 

### Review Pricing Wizard data

This will provide a summary of the data stored in `user_data.json`

## Unit Tests

There are some small tests which have been written to check different packages are working as intended. The intended outcome here is not to have any errors. To run them, copy the following into your terminal.

```
for ut in `ls ut*.py`; do
  python3 $ut
  if [[ $? != 0 ]]; then
    echo "Failed test for $ut"
  fi
done
```

## Tutorial For Setup

We are using git to manage version control for this tool.

### First Time Usage

You will need to ensure you have git credentials setup. You can either use a username/password login or you can use an SSH key.

Details can be found [here](https://docs.github.com/en/get-started/getting-started-with-git/about-remote-repositories) but basically:

  - If you are using a username/password - *Use HTTPS clone*
  - If you are using an SSH key - *Use SSH clone*

In the terminal window

*HTTPS clone*
```
git clone https://github.com/grprshikhar/pricing_dev.git
```

*SSH clone*
```
git clone git@github.com:grprshikhar/pricing_dev.git
```

### Updating Repository

When the tool is developed, updates will be pushed to the main repository. In order to benefit from these changes, you need to _pull_ the updated repository locally. If you have made changes to any files, you may be asked to stash or revert them.

*Pulling updated repository*

Run the following command in your repository:

```
git pull
```

You should see information about what was updated.

*Changes to user_data.json*

If you have editted the `user_data.json` file, you may see a warning which prevents your repository from being updated. In this case, you should do the following:

  - Copy the current file and revert the original
    - `cp user_data.json user_data_bkup.json`
    - `git checkout user_data.json`
  - After you update the repository (with `git pull`), you should compare the two files and update as appropriate. Most likely, the change will be minimal and specific to your user.

### Alias

An alias is the equivalent of a shortcut within the terminal infrastructure. Depending on your shell, you should have a .bashrc or a .zshrc in your home area. Run `echo $SHELL` to see whether you are using `/bin/bash` or `/bin/zsh`. For either of these, you should have a file which can handle aliases and paths in `~/.bashrc` and `~/.bash_profile` or `~/.zshrc` and `~/.zprofile`. These are files which are automatically sourced when your terminal starts (rc or profile depends on the connection you are using).

Inside *this* folder (eg `pricing_wizard/`) after you have cloned it, you can run the following command to make a permanent command `pricing_wizard` which you can run from any location in your terminal. You only need to set this up once.

For /bin/bash:
```
touch ~/.bashrc
touch ~/.bash_profile
export PWPATH=$PWD
echo "alias pricing_wizard='cd $PWPATH; python3 pricing_wizard.py'" >> ~/.bashrc
echo "alias pricing_wizard='cd $PWPATH; python3 pricing_wizard.py'" >> ~/.bash_profile
```

For /bin/zsh
```
touch ~/.zshrc
touch ~/.zprofile
export PWPATH=$PWD
echo "alias pricing_wizard='cd $PWPATH; python3 pricing_wizard.py'" >> ~/.zshrc
echo "alias pricing_wizard='cd $PWPATH; python3 pricing_wizard.py'" >> ~/.zprofile
```





































