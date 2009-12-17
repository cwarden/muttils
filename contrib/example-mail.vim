" $Id: example-mail.vim,v 4d3acc66b2ca 2007-09-08 01:02 +0200 blacktrash $
" set up sigpager eg. in ~/.vim/after/ftplugin/mail.vim

" choose email signature, append at EOF, jump back to previous position
nnoremap <buffer> <LocalLeader>s m`:$r!sigpager<CR>:redr!<CR>``
