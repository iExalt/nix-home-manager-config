" Enable line numbers
set number

" Enable syntax highlighting
syntax on

" fix(vim): avoid OSC color-query stalls through Zellij.
if exists("$ZELLIJ")
  set t_RF= t_RB=
endif
