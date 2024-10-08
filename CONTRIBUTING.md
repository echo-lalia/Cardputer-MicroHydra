# Contributing to MicroHydra!

>**Note:** *These guidelines only apply to the main MicroHydra program. There are no restrictions to the design or functionality of apps for MH.*

<br/>
<br/>

## Overview on communicating and sharing your changes:

<br/>

### - If you'd like to contribute a fix, or enhancement to MicroHydra, consider making an issue for it before getting to work.
This will aide in communication with other contributors, and give a convenient space to discuss the topic.   
*Note: If you've already made your changes, feel free to just submit a pull request.*

---

### - Create a personal fork, and implement your changes   
Try keeping it to one topic at a time, and if your changes are somewhat complex, make sure to test as you go.   
*Sometimes the behavior can differ when run directly from Thonny, vs running on the device on its own.*

---

### - Test what you can, and let me know about it
MicroHydra needs to be tested both on a plain MicroPython install, and as a complete firmware.  
Changes also need to be tested on multiple devices before they are released in a stable build.

You aren't expected to do all the testing yourself, but if you can do *some* testing, and let me know what testing you did, it is a huge help!

> *Don't worry about this too hard if you're making relatively small changes; especially ones that only affect one app. I'll merge it and just test it along with my own changes before releasing the next version.*

---

### - Consider updating the contents of `wiki/` to reflect your changes
This repo automatically publishes changes made in the `wiki/` directory to the 'wiki' tab on GitHub.  
If your changes make some information on the wiki outdated, it would be very helpful for you to update the wiki to communicate your changes, as well.

---

### - Create a pull request with a summary of your changes, and link the pull request to the issue (if it exists)
Once it's been reviewed, if no further changes need to be made to it, it'll be pulled to the main repo, and the issue will be closed

<br/>

*If you have any concerns or questions about this workflow, feel free to reach out!*

---


<br/>
<br/>
<br/>
<br/>
<br/>
<br/>
<br/>



> *The rest of this guide can probably be ignored for most contributions, but provide further details on MicroHydra's design for those who are interested:*

## Guidelines and philosophy for core MicroHydra functionality

<br/>

### - One of MicroHydra's earliest goals was accessibility.   

This project aims to encourage tinkerers, makers, and developers, both experienced and completely new, to use and create apps for their Cardputers. The design for the app loading system was created with this in mind.    
By only requiring a simple .py file to be placed in the /apps folder, and restarting between apps, MH is able to support even extremely basic MP scripts, with little to no modificaiton. And more complex programs, which require additional libraries or other files, can simply point their fetch those files from a subfolder of the apps folder (or anywhere else).

Another way MicroHydra aims to be accesible, is by providing a large amount of documentation on the use of the launcher, and on the use of the libraries that come with it.    
It is a goal of mine to keep the wiki updated with answers to common questions, and provide examples, and instructions, to help new developers make apps or contributions for MH. 

And a final note on accesibility; This launcher is intended to work on "plain MicroPython". This is important because it minimizes restrictions on the version of MicroPython that MicroHydra can work with, and therefore reduces restrictions on the kinds of apps that can be made for MicroHydra.   
For example, if you had an ambitious idea for a game, and you wanted to use a display driver such as [s3lcd](https://github.com/russhughes/s3lcd) *(which is provided as a custom C module in a compiled MicroPython firmware)*.   
If MicroHydra was only available as a compiled firmware, you would be unable to combine s3lcd and MicroHydra, without compiling your own MicroPython from source. This could cause new barriers-to-entry, and pontentially prevent some very cool ideas from ever getting started.

### - Stability is highly important.

Another thing that is important for MicroHydra, is it's ability to just work without requiring a ton of technical knowledge, or troubleshooting.   
I've abandonded some really cool features for the launcher due to stablity reasons, and will probably do it again in the future. Providing something that is feature-rich and behaves like a real operating system would be very cool, but MicroHydra's primary responsibility is just to start 3rd party apps, and it needs to be good at that. 

<br/>


## Code Style

<br/>

*As mentioned above, MicroHydra was originally created quickly and messily. Not all of these suggestions are fully implemented in existing code, but these are goals for future code in MicroHydra.* 

### - Tabs or Spaces?
I started MicroHydra with spaces for indentation, as that is the standard method that came with my editor. However, I have come to prefer tabs for [accessibility](https://adamtuttle.codes/blog/2021/tabs-vs-spaces-its-an-accessibility-issue/) reasons.   
I was planning on totally replacing all the space-indents with tab characters because of this. However, I stopped myself because there were already contributors working on this project, and I did not want to cause further issues/confusion because of this change. Especially because some people who wish to contribute to MicroHydra are new programmers, and requiring contributors to change their editors settings before working on MH, would just be an additional barrier.   
So, for now, I am adopting an intentionally relaxed stance on indentation for MicroHydra. As long as you do not mix tabs/spaces in a single file, you can choose whichever you prefer. 

### - Naming Conventions
For a quick reference, this is the current (intended) state of MH's variable naming style:
```
modulename
_NAMED_CONSTANT
GLOBAL_VARIABLE
ClassName
function_name
regular_variable
```
This is mostly a (simplified) reflection of [PEP 8](https://peps.python.org/pep-0008/) standards. However, with the intentional change of using a leading underscore in the name of a constant. This is because MicroPython supports [*'real'* constants](https://docs.micropython.org/en/latest/develop/optimizations.html#variables) through the use of the `const` keyword + that leading underscore.


### - Comment heavily!
As MicroHydra is intended to be accessible and approachable, I highly recommend using many comments in your code! It takes only a small amount of extra storage, uses no memory at all, and makes your code much more understandable for beginners.   
I'm a particular fan of using large, flashy, blocks of comments to split code into sections, and adding comments which explain why one piece of code might be using a different approach than you would first expect. 
