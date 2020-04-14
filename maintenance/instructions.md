# Run CEQR recipe

## Trigger a check
+ From the front page of the repository, navigate into the `maintenance` folder.

+ In `maintenance` you will see the following files: 
    + `instructions.md`
    + `log.md`
    
    Edit the `log.md` file to trigger the build process.

+ To edit `log.md`, click on `log.md`, and then click the pencil button, which is highlighted by the red box in the image below

+ A file editor will pop open and now you can add a new entry to the end of the build log. Make sure you are following the format highlighted in the screenshot and provided below.

`## year/month/date -- name`
`+ which recipe did you run?`
`+ some comments here`
`+ some other comments here`

+ Once you are done editing `log.md`, you are ready to commit the change to the `master` branch and trigger the build. To do this, scroll to the bottom of the page below the text editor to where it says "Commit changes."  **Give your commit a title and make sure that it includes the name of the recipe you'd like to build, e.g. `sca_capacity_projects`,** and enter an optional description. It is important that you include the recipe name in the commit title so that github Actions will be triggered.


Select "Commit directly to master branch" and click __commit changes__

+ Now head to github actions by selecting "Actions" in the main banner.

+ You will see that the build you specified has been triggered.

+ Confirm that the build was successful by making sure a green check appears next to the action.