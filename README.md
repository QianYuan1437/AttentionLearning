
### 1、git命令学习
删除本地分支：git branch -d localBranchName

删除远程分支：git push origin --delete remoteBranchName

查看分支：git branch

创建分支：git branch <name>

切换分支：git checkout <name>或者git switch <name>

创建+切换分支：git checkout -b <name>或者git switch -c <name>

合并某分支到当前分支：git merge <name>

删除分支：git branch -d <name>

某分支的更改合并到main分支：

1、先切换到main分支：git checkout main

2、合并某分支到main分支：git merge <name>

3、推送main分支到远程：git push origin main
