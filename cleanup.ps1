$limit = (Get-Date).AddDays(-3)

Get-ChildItem -Path "user_uploads\*" -File |
    Where-Object {$_.CreationTime -lt $limit} |
    Remove-Item -Force

Get-ChildItem -Path "workspace\*" -Directory |
    Where-Object {$_.CreationTime -lt $limit} |
    Remove-Item -Recurse -Force
