import readchar
# Manually handle password input
# ESC - Show/Hide password
# CTRL_C/D - Exit prompt
# Handle backspace correctly in show/hide mode
# Handle printing input to terminal in both cases

def getpass(prompt):
	print("Press ESC to show/hide password; CTRL+C/CTRL+D to exit")
	print(prompt, end='', flush=True)
	buf = ''
	hidden = True
	while True:
		ch = readchar.readchar()
		if ch == readchar.key.ENTER:
			print('')
			break
		elif ch == readchar.key.BACKSPACE:
			buf = buf[:-1]
			print('\r'+prompt+' '*(len(buf)+1), end='', flush=True)
			if hidden:
				print('\r'+prompt+'*'*len(buf), end='', flush=True)
			else:
				print('\r'+prompt+buf, end='', flush=True)
		elif ch == readchar.key.CTRL_C:
			raise KeyboardInterrupt("Cancelling Admin Panel")
		elif ch == readchar.key.CTRL_D:
			raise KeyboardInterrupt("Cancelling Admin Panel")
		elif ch == readchar.key.ESC:
			if hidden:
				hidden = False
				print('\r'+prompt+buf, end='', flush=True)
			else:
				hidden = True
				print('\r'+prompt+'*'*len(buf), end='', flush=True)
		else:
			buf += ch
			if hidden:
				print('*', end='', flush=True)
			else:
				print(ch, end='', flush=True)
	return buf
