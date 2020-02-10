" Make Vim more useful
set nocompatible
" Use the OS clipboard by default (on versions compiled with `+clipboard`)
set clipboard=unnamed
" Enhance command-line completion
set wildmenu
" Allow backspace in insert mode
set backspace=indent,eol,start
" Optimize for fast terminal connections
set ttyfast
" Add the g flag to search/replace by default
set gdefault
" Use UTF-8
set encoding=utf-8
" Change mapleader
let mapleader=","
" Centralize backups, swapfiles and undo history
if empty(glob('~/.nvim/backups'))
    silent !mkdir -p ~/.nvim/backups
endif
set backupdir=~/.nvim/backups
if empty(glob('~/.nvim/swaps'))
    silent !mkdir -p ~/.nvim/swaps
endif
set directory=~/.nvim/swaps
if empty(glob('~/.nvim/undo'))
    silent !mkdir -p ~/.nvim/undo
endif
set undodir=~/.nvim/undo

" Respect modeline in files
set modeline
" Enable per-directory .vimrc files and disable unsafe commands in them
set exrc
set secure
" Toggle line numbers with ,l
map <leader>l <ESC>:exec &number==1 ? "set nonumber" : "set number"<CR>
" Enable syntax highlighting
syntax on
" Make tabs as wide as four spaces
set tabstop=4
" Show tabs and spaces
set lcs=tab:▸\ ,trail:·
" Toggle above with ,L
map <leader>L <ESC>:exec &list==1 ? "set nolist" : "set list"<CR>
" Highlight searches
set hlsearch
" Ignore case of searches
set ignorecase
" Highlight dynamically as pattern is typed
set incsearch
" Always show status line
set laststatus=2
" Toggle mouse with ,m
map <leader>m <ESC>:exec &mouse!=""? "set mouse=" : "set mouse=a"<CR>
" Show the cursor position
set ruler
" Don’t show the intro message when starting Vim
set shortmess=atI
" Show the current mode
set showmode
" Show the filename in the window titlebar
set title
" Show the (partial) command as it’s being typed
set showcmd
" Start scrolling three lines before the horizontal window border
set scrolloff=3

" Strip trailing whitespace (,ss)
function! StripWhitespace()
	let save_cursor = getpos(".")
	let old_query = getreg('/')
	:%s/\s\+$//e
	call setpos('.', save_cursor)
	call setreg('/', old_query)
endfunction
noremap <leader>ss :call StripWhitespace()<CR>
" Save a file as root (,W)
noremap <leader>W :w !sudo tee % > /dev/null<CR>

" Automatic commands
if has("autocmd")
	" Enable file type detection
	filetype on
	" Treat .json files as .js
	autocmd BufNewFile,BufRead *.json setfiletype json syntax=javascript
	" Treat .md files as Markdown
	autocmd BufNewFile,BufRead *.md setlocal filetype=markdown
endif

" Specify a directory for plugins
call plug#begin(stdpath('data') . '/plugged')

Plug 'neoclide/coc.nvim', {'branch': 'release'}
Plug 'mdempsky/gocode', { 'rtp': 'vim', 'do': '~/.vim/plugged/gocode/vim/symlink.sh' }
Plug 'Shougo/defx.nvim', { 'do': ':UpdateRemotePlugins' }
Plug 'scrooloose/nerdTree'
Plug 'neomake/neomake'

call plug#end()

source ~/.config/nvim/coc.vim

nmap <C-n> :NERDTreeToggle<CR>
call neomake#configure#automake('nrwi', 500)
