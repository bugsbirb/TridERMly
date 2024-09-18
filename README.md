[![CodeFactor](https://www.codefactor.io/repository/github/bugsbirb/TridERMly/badge)](https://www.codefactor.io/repository/github/bugsbirb/TridERMly)
# 🤯 TridERMly
> It's a roblox moderation bot that I decided to upload and open source. You can use the code to learn off or if you want to you can actually use it in a server.
> You can contribute to this project if you'd like by opening a pull request; the code has to be quality tho.
> Don't judge the code no one is perfect.

### .env
> Make sure to actually remove the comment and rename template.env to .env so it actually works.
A Mongo URL is https://www.mongodb.com.
```env
Remove this comment and rename the file to .env

TOKEN=
prefix=>
MONGO_URL =

```

### config.yaml
> Fill it out so the bot actually works
```yaml
# ----------------- CONFIG.YAML DESCRIPTIONS ----------------- (You can delete this if you want.)

# LOA
# -----------------
#  channel: The channel where the requests get sent
#  role: The LOA Role
#  permissions: The role that can send requests


# Shifts
# -----------------
#  channel: The channel where the requests get sent
#  permissions: The roles that can send requests
#  online: The role that can be online
#  break: The role that can be on break
#  manager: The roles that can manage the shifts


# Punishments
# -----------------
#  channel: The channel where the requests get sent
#  types: The types of punishments that can be given
#  permissions: The roles that can give punishments
 
 
shifts:
 channel: 
 permissions: [] 
 online:
 break: 
 manager: [] 
 

punishments:
 channel: 
 types: ['Warning', 'Kick', 'Ban']
 permissions: []
 
 
loa:
 channel:  
 role:  
 permissions: []
 manager: [] 
```

### 🙌 Contributions
> You can contribute to this project if you'd like by opening a pull request; the code has to be quality tho.
