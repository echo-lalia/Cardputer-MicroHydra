# Contributing to MicroHydra!

MicroHydra started with very fast and chaotic developnment, designed by one person, and with new features and complete overhauls added almost daily. 

Now that there are multiple people interested in implementing new features and improvements to MH, as well as people designing apps to be used with MH, I thought it would be best to create some contribution guidelines to help us work together more easily, and prevent things from getting broken haphazardly. 

**Note:** *These guidelines only apply to the main MicroHydra program. There are no restrictions to the design or functionality of apps for MH.*

<br/>
<br/>
<br/>

## Overview on communicating and sharing your changes:

### If there's a problem with MicroHydra, or if you have an idea for an improvement or addition you'd like to see, create an issue for it.   
This will aide in communication with other contributors for this project, by creating a space to dicuss a particular change, and by allowing you (or another contributor) to assign yourself to the issue, to signal that you are working on it.   

### Once you've assigned yourself to an issue, create a personal fork, and implement your changes   
Try keeping it to one issue at a time, and make sure you're testing the changes you make as you go. Sometimes the behavior can differ when run directly from Thonny, vs running on the device on its own.

### Test your changes on a normal MicroPython install
Because MicroHydra is indended to be capable of running uncompiled, on a plain install of MicroPython, it's important that it be tested like this, as well.
The code will generally use less memory and be more stable when compiled, so it's important that the changes it be tested uncompiled, on it's own (not through thonny / REPL) on a regular MicroPython install.   
If it works like that, it should usually work even better once compiled. If for any reason you are unable to test it yourself, or you would like a second opinion on it, let me know. 

### Create a pull request with a summary of your changes, and link the pull request to the issue
Once it's been reviewed, if no further changes need to be made to it, it'll be pulled to the main repo, and the issue will be closed

*If you have any concerns or questions about this workflow, feel free to reach out!*



<br/>
<br/>
<br/>






## Guidelines and philosophy for core MicroHydra functionality

#### One of MicroHydra's earliest goals was accessibility.   

This project aims to encourage tinkerers, makers, and developers, both experienced and completely new, to use and create apps for their Cardputers. The design for the app loading system was created with this in mind.    
By only requiring a simple .py file to be placed in the /apps folder, and restarting between apps, MH is able to support even extremely basic MP scripts, with little to no modificaiton. And more complex programs, which require additional libraries or other files, can simply point their fetch those files from a subfolder of the apps folder (or anywhere else).

Another way MicroHydra aims to be accesible, is by providing a large amount of documentation on the use of the launcher, and on the use of the libraries that come with it.    
It is a goal of mine to keep the wiki updated with answers to common questions, and provide examples, and instructions, to help new developers make apps or contributions for MH. 

And a final note on accesibility; This launcher is intended to work on "plain MicroPython". This is important because it minimizes restrictions on the version of MicroPython that MicroHydra can work with, and therefore reduces restrictions on the kinds of apps that can be made for MicroHydra.   
For example, if you had an ambitious idea for a game, and you wanted to use a display driver such as [s3lcd](https://github.com/russhughes/s3lcd) *(which is provided as a custom C module in a compiled MicroPython firmware)*.   
If MicroHydra was only available as a compiled firmware, you would be unable to combine s3lcd and MicroHydra, without compiling your own MicroPython from source. This could cause new barriers-to-entry, and pontentially prevent some very cool ideas from ever getting started.

#### Stability is highly important.

Another thing that is important for MicroHydra, is it's ability to just work without requiring a ton of technical knowledge, or troubleshooting.   
I've abandonded some really cool features for the launcher due to stablity reasons, and will probably do it again in the future. Providing something that is feature-rich and behaves like a real operating system would be very cool, but MicroHydra's primary responsibility is just to start 3rd party apps, and it needs to be good at that. 

<br/>


## Code Style

*As mentioned above, MicroHydra was originally created quickly and messily. Not all of these suggestions are fully implemented in existing code, but these are goals for future code in MicroHydra.* 

#### Tabs or Spaces?
I started MicroHydra with spaces for indentation, as that is the standard method that came with my editor. However, I have come to prefer tabs for [accessibility](https://adamtuttle.codes/blog/2021/tabs-vs-spaces-its-an-accessibility-issue/) reasons.   
I was planning on totally replacing all the space-indents with tab characters because of this. However, I stopped myself because there were already contributors working on this project, and I did not want to cause further issues/confusion because of this change. Especially because some people who wish to contribute to MicroHydra are new programmers, and requiring contributors to change their editors settings before working on MH, would just be an additional barrier.   
So, for now, I am adopting an intentionally relaxed stance on indentation for MicroHydra. As long as you do not mix tabs/spaces in a single file, you can choose whichever you prefer. 

#### Naming Conventions
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


#### Comment heavily!
As MicroHydra is intended to be accessible and approachable, I highly recommend using many comments in your code! It takes only a small amount of extra storage, uses no memory at all, and makes your code much more understandable for beginners.   
I'm a particular fan of using large, flashy, blocks of comments to split code into sections, and adding comments which explain why one piece of code might be using a different approach than you would first expect. 
