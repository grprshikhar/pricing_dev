from modules.options_handler import options_handler as opts

pricing_wizard = opts()
pricing_wizard.validate_user()
pricing_wizard.select_sheet()
pricing_wizard.info()