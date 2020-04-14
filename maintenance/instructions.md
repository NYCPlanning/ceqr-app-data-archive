# Run GRU QAQC checks

## Trigger a check
+ From the front page of the repository, navigate into the `maintenance` folder.

+ In `maintenance` you will see the following files: 
    + `instructions.md`
    + `log.md`
    
    We're going to edit the `log.md` file to trigger the build process.

+ To edit `log.md`, click on `log.md`, and then click the pencil button, which is highlighted by the red box in the image below

+ A file editor will pop open and now you can add a new entry to the end of the build log. Make sure you are following the format highlighted in the screenshot and provided below.

`## year/month/date -- name`
`+ some comments here`
`+ some other comments here`

+ Once you are done editing `log.md`, you are ready to commit the change to the `master` branch and trigger the build. To do this, scroll to the bottom of the page below the text editor to where it says "Commit changes."  **Give your commit a title and make sure that it includes the name of the check you'd like to run, e.g. `[atomic-polygon]`,** and enter an optional description.	It is important that you include the check name in the commit title so that github Actions will be triggered.

Currently, the following checks are available:
- **`[atomic-polygon]`**
- **`[address-points]`**
- **`[footprints]`**
- **`[housing]`**

If you would like to trigger a few QAQC checks at once, be sure to include multiple key words. For example, include **'`[atomic-polygon][address-points]`'** to run two tests.

If you would like to trigger **all** QAQC tests, you can include the phrase **`[all]`**.

Select "Commit directly to master branch" and click __commit changes__

+ Now head to github actions by selecting "Actions" in the main banner.

+ You will see that the check you specified has been triggered.

+ Confirm that the check was successful by making sure a green check appears next to the action.  If a red X appears reach out to a team member.

+ If the QAQC process was successful, you're now ready to download the results. Links to download the latest version  of QAQC results are in the README on the repo's main page.
