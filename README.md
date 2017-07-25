# Research Practicum - Team Busted 

[![Build Status](https://travis-ci.com/LookOnTheBrightSide/busted_app.svg?token=67ZRMCE3p6XpMKUH71z1&branch=master)](https://travis-ci.com/LookOnTheBrightSide/busted_app)

![accubus logo](https://s21.postimg.org/ygezrvzrb/Screen_Shot_2017-07-20_at_09.00.03.png)

The live site is available here: [Accubus](http://accubus.info/)

This is the documentation for Team Busted. A basic guide on how to set up your development environment will be detailed below. We use two GitHub repositories, one for misclelenous code that's written for the project (i.e Formatting data, cleaning up data etc). Our second repository is of the main application itself. This is the actual codebase for the deployed application. 

## Version Control
We use Git and GitHub to manage our source code.
## GitFlow
We use a branching model for Git called GitFlow. We are not adhering to the complex nature of the original version, we have watered it down but we still mantain it's core idea. We have a ```development``` branch and a ```master``` branch. All contributors branch off the development branch and develop features on there. Before pushing their branch to be merged on the development branch, they should make sure to ```git pull``` so as to get any recent changes on the ```development``` that might have been added. Before pushing, the contributor should also make sure that all intergration tests are passing.

## Code Reviews

Once code has been pushed and a pull request made, other members of the team must review the code and leave a "thumbs up" emoticon if they're happy with the code otherwise leave comments outlining what could be improved (etc).

## Merging code

Feature branches are merged after they've gone through a code review. Each feature branch must at least get 2 thumbs ups(contributor approvals) before being merged. 

Code on the ```development``` branch is merged into the ```master``` branch at the end of the sprint. 

* Contributors should not merge their own branches

## Test Driven Development

We take a test driven approach in developing our project. We write failing tests first then the code to make them pass. After the tests pass, time should be spent on refactoring the code.

### Code Styleguide

For Python we follow the PEP8 styleguide. This styleguide gives details pertaining to issues such as variable naming, code folding e.t.c
Details can be found [here](https://www.python.org/dev/peps/pep-0008/)

For JavaScript we follow Google's style guide. 
Details can be found [here](https://google.github.io/styleguide/javascriptguide.xml)

### We use the following:

###### Video conferencing
[Appear](https://appear.in/) 
For days that we can't come into college
###### Documents
[GoogleDocs](https://www.google.com/docs/about/) 
General documentation, meeting minutes, retrospective, 
###### Project management
[Jira](https://jira.com/)
Project management, Kanban, Burndown Chart, Task management
##### Messaging
[Slack](https://slack.com/) 
Instant messaging
##### Continuous Integration
[Travis](https://travis-ci.com/) 
Continuous Integration and testing builds
##### Source code management
[Git](https://git-scm.com/) and [Github](https://github.com/) 
Source code management, version control

### Branching naming for Git
Branch names are prefixed by the collaborator's initials. Names should be descriptive. (see examples below)

```nn_create_mongodb_database```

```co_make_app_footer```

```gh_display_station_graph```

```tl_render_time_json```

e.t.c


## Server Side

```$ ssh root@178.62.29.173```

* note that password log in is disabled. You need the private key to gain access.

From inside the mongo shell you need to run the following to index the gps locations

```$ mongo```

`> use accubusDB`

`> db.stops.createIndex( { location: "2dsphere" } )`

### Main app:
```$ /srv/AppEnv/appdata```

### Binaries

```$ /srv/AppEnv/```

### Start/Stop MongoDB 

```$ sudo systemctl start mongodb```

```$ sudo systemctl stop mongodb```

### Start/Stop Application

The following must be executed if any changes are made to the app.

```$ systemctl start emperor.uwsgi```

```$ systemctl stop emperor.uwsgi```

### App logs

```$ /srv/AppEnv/uwsgi.log```
