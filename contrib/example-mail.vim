" $Id$
" set up sigpager eg. in ~/.vim/after/ftplugin/mail.vim

function! s:Sigpager()
  " appends signature chosen via sigpager at end of file
  "
  " in some terminals reading sigpager output from stdout prepends control
  " characters, use a temporary file to read from instead of a simple
  " :silent! $ read !sigpager

  let l:sig = tempname()
  silent execute "!sigpager" l:sig
  execute "$ read" l:sig
  execute "call delete('" l:sig "')"
  redraw!
endfunction

" choose email signature, append at EOF, jump back to previous position
nnoremap <buffer> <LocalLeader>s m`:call <SID>Sigpager()<CR>``
