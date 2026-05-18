" Enable line numbers
set number

" Enable syntax highlighting
syntax on

" fix(vim): avoid OSC color-query stalls through Zellij.
if exists("$ZELLIJ")
  set t_RF= t_RB=
endif

" fix(vim): make Alt word motion symmetric across terminals.
execute "set <M-b>=\eb"
execute "set <M-f>=\ef"

nnoremap <M-Left> b
nnoremap <M-Right> w
nnoremap <M-b> b
nnoremap <M-f> w

inoremap <M-Left> <C-o>b
inoremap <M-Right> <C-o>w
inoremap <M-b> <C-o>b
inoremap <M-f> <C-o>w

vnoremap <M-Left> b
vnoremap <M-Right> w
vnoremap <M-b> b
vnoremap <M-f> w
