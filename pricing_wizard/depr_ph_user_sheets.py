import inquirer
from inquirer.themes import load_theme_from_dict
from termcolor import colored,cprint
import sys

export_dict = {
    'Achille' : {'E-Price':'1xNa_gKhmPXaXI2_gTULOPQ5z_jG6xoVKg7G9I5OXIj8',
            'Catman GM' : '', 
            'US Catman GM':''},
    'Geet' : {'E-Price':'1xNa_gKhmPXaXI2_gTULOPQ5z_jG6xoVKg7G9I5OXIj8',
            'Catman GM' : '', 
            'US Catman GM':''},
    'Marco' : {'E-Price':'1xNa_gKhmPXaXI2_gTULOPQ5z_jG6xoVKg7G9I5OXIj8',
            'Catman GM' : '', 
            'US Catman GM':''},
    'Mert' : {'E-Price':'1xNa_gKhmPXaXI2_gTULOPQ5z_jG6xoVKg7G9I5OXIj8',
            'Catman GM' : '', 
            'US Catman GM':''},
    'Shikhar' : {'E-Price':'1xNa_gKhmPXaXI2_gTULOPQ5z_jG6xoVKg7G9I5OXIj8',
            'Catman GM' : '', 
            'US Catman GM':''},
    'Ian' : {'E-Price': '1r_LxoZd33ewZhPt9hp8lda4RPU05F94PWrgML1-PocU',
            'Catman GM' : '', 
            'US Catman GM':''},
}



inq_theme = load_theme_from_dict({
    "Question": {
        "mark_color": "yellow",
        "brackets_color": "normal",
        
    },
    "List": {
        "selection_color": "black_on_bright_green",
        "selection_cursor": "->"
    }
})


question_user = [
    inquirer.List(
        "user",
        message="Who are you?",
        choices=list(export_dict.keys()) + ["None of the above"],
    ),
]



def get_user():
    confirm_user='no'
    while confirm_user=='no':
        print("\n")
        answer_user = inquirer.prompt(question_user,theme=inq_theme)
        print("\nYou entered: " + colored(answer_user['user'],'green')+"\n")
        confirm_user = input("Is this correct ([yes]/no/exit) : ")
        confirm_user = confirm_user.lower()
        if confirm_user == "" :
            confirm_user = "yes"
        if confirm_user not in ['yes','no','exit']:
            print(colored("Incorrect response!",'red'),"\n\nPlease use only (yes/no/exit)\n")
            confirm_user='no'
        elif confirm_user=='exit' or answer_user['user']=='None of the above':
            print("\n\nYou selected 'exit' or you are not authorized here. Exiting wizard now...\n\nBye!\n\n")
            sys.exit()

    return answer_user['user']

def sheet_output(user):
    message_in = "Source of export? (User Name: "+user+")"
    question_sheet = [
        inquirer.List(
            "sheet_name",
            message=message_in,
            choices=["E-Price", "Catman GM", "US Catman GM", "Other"],
        ),
    ]
    return question_sheet


def get_sheet(user,export_dict):
    confirm_sheet='no'
    while confirm_sheet=='no':
        print("\n")
        answer_sheet = inquirer.prompt(sheet_output(user),theme=inq_theme)
        print("\nYou entered: " + colored(answer_sheet['sheet_name'],'green')+"\n")
        confirm_sheet = input("Is this correct ([yes]/no/exit): ")
        confirm_sheet = confirm_sheet.lower()
        if confirm_sheet == "":
            confirm_sheet = "yes"
        if confirm_sheet not in ['yes','no','exit']:
            print(colored("Incorrect response!",'red'),"\n\nPlease use only (yes/no/exit)\n")
            confirm_sheet='no'
        elif confirm_sheet=='exit':
            print("\n\nYou selected 'exit'. Exiting wizard now...\n\nBye!\n\n")
            sys.exit()
    
    
    
    if answer_sheet['sheet_name']=='Other':
        confirm_filexls='n'
        while confirm_filexls=='n':
            SPREADSHEET_ID = input("Please enter SPREADSHEET_ID: ")
            # files_xls = files_xls
            print("\nYou entered: " + colored(SPREADSHEET_ID,'green')+"\n")
            confirm_filexls = input("Is this correct (yes/no/exit): ")
            confirm_filexls=confirm_filexls.lower()
            if confirm_filexls not in ['yes','no','exit']:
                print(colored("Incorrect response!",'red'),"\n\nPlease use only (yes/no/exit)\n")
                confirm_filexls='no'
            elif confirm_filexls=='exit':
                print("\n\nYou selected 'exit'. Exiting wizard now...\n\nBye!\n\n")
                sys.exit()
        outsheet = SPREADSHEET_ID
    else:
        outsheet = export_dict[user][answer_sheet['sheet_name']]
    
    return outsheet




