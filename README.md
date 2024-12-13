# Memorize

A Sublime Text plugin to help with keeping track of various file locations and visualizing them as a stack.

<img width="1920" alt="image" src="https://github.com/user-attachments/assets/6696ebf4-73b7-4fb4-b34e-d820321a3a7c" />

## Commands
* Add frame.
  * Creates a new frame from the current file, cursor location and active selection.
  * If there's an active selection, the frame will include all text in the selection.
  * Automatically shows the current stack. This behaviour can't be disabled yet, but will be doable shortly through settings.
  * DOES NOT properly support multiple selections yet.
* Jump to next frame
  * Loops around when hitting either end of the stack.
  * If the frame refers to a file that is not currently open, it will be opened and cursor placed at the frame location.
* Jump to previous frame
* Show stack
  * Opens a new stack view tab if it's not currently showing.
  * It will show an empty stack even if there are no frames.
* Clear stack
  * Removes all saved frames.
  * Automatically closes the stack view if one is open.
* Hide stack
  * Closes any open stack view, but does not remove any frames.
  * Jumping between stack frames works fine even when the stack is hidden.

## Default Keybindings
The default keybindings are disabled, but you can enable or change them using the command palette option.
<img width="606" alt="image" src="https://github.com/user-attachments/assets/ad54870b-155f-4d09-aa3f-7f67d7ab5fd6" />
