# Pricing Wizard

## Table of Contents

- [Pricing Wizard](#pricing-wizard)
  * [Table of Contents](#table-of-contents)
  * [Introduction](#introduction)
  * [Systems](#systems)
    + [Mac OSX](#mac-osx)
    + [Windows](#windows)
  * [Usage](#usage)
    + [Reprice SKUs](#reprice-skus)
    + [Price new SKUs](#price-new-skus)
    + [Run report](#run-report)
    + [Suggest price review SKUs](#suggest-price-review-skus)
    + [Review Pricing Wizard data](#review-pricing-wizard-data)


## Introduction

This tool is attempting to standardise the checks we need to apply before prices go live on the Grover website.
It is important that as we scale up, we have tools which can manage increasing the numbers of SKU in a consistent manner.
We currently will still make use of Google Sheets but will start to implement checks and streamline the upload processes.

## Systems

The hope is that with the aid of Google Drive, we will not need to have a central location (ie AWS) to use this tool, but instead it can be used locally by any pricing analyst using a device which complies with Grover security requirements (eg encrypted, VPN access, centrally managed).

### Mac OSX

This tool has been developed on OSX and should therefore not require much work from the user to get it running.

 - python3
   - Install using [homebrew](https://brew.sh/)
   - `brew install python3` and follow the finalisation instructions
   - Install requirements using `pip3 -r requirements`

### Windows

This is where things might be bumpy at first. The best working solution is to use [Windows subsystem for Linux](https://docs.microsoft.com/en-us/windows/wsl/install) which is available for Windows 10/11. This is a Microsoft supported system which allows a Linux installation to be made within the Windows environment. Further information regarding setup can be found in [this article](https://pbpython.com/wsl-python.html).

Moving forwards, the most sensible Linux OS to choose is `Ubuntu 20.X`. Some information regarding setting up `python3` is available in [this article](https://linuxize.com/post/how-to-install-python-3-9-on-ubuntu-20-04/). 

A brief summary is:
 - `sudo apt-get update`
   - This will update the package manager.
 - `sudo apt install software-properties-common`
   - This will install requirements for python3.9
 - `sudo add-apt-repository ppa:deadsnakes/ppa`
   - This will add the repository which contains modern python3.X releases
 - `sudo apt-get install python3.9`
   - This will ask the package manager to install python3.9.
 - `pip3 -r requirements`
   - This should be the same as the OSX instructions to install the required modules.

## Usage

This tool is written for `python3` and makes use of standard data manipulation libraries (such as `pandas`).
The tool has the ability to access the data stored in Google Sheets and Google Drive which are shared with `Grover` or the `pricing_analytics` user.
The tool expects active user input to direct the workflow and verify any warnings. In some cases, there will be errors which have been identified which will require pricing analyst intervention but the aim is to limit these to the cases where there are issues with the chosen price points.

```
./pricing_wizard.py
```

This will start the tool and provide a list of options:

1) Reprice SKUs
2) Price new SKUs
3) Run report
4) Suggest price review SKUs
5) Review Pricing Wizard data
6) Exit

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



