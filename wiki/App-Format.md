## Format of MicroHydra apps:
MicroHydra apps can be placed in the apps folder on the device's main storage, or in the apps folder on an SD Card (The launcher will create these folders automatically if they don't exist.)

<br/>

All that is needed to make a valid MicroHydra app, is a .py file *(or a compiled .mpy file)* with some MicroPython code placed in the apps folder.   
The file name becomes the app name, and it will be imported by main.py when launched using MicroHydra.   
This is the simplest form of a MH app, and several apps in the [apps](https://github.com/echo-lalia/MicroHydra-Apps) repo are designed like this. 

<br/>

Apps that are more complex can be made as a folder, instead. This can allow you to bundle in dependencies, or split the code up into multiple files for better readability. A MicroHydra app as a folder works essentially the same as a normal Python module, where a file named `__init__.py` inside that folder will be imported at launch.

If you decide to format your app as a folder, you'll probably want to use 'relative' imports to access the other modules in the app folder.   
However, relative imports don't work when running from the editor. My usual solution to this is to use both relative, and absolute imports, in a try/except statement. Here's what that looks like:

``` Python
try:
    # relative import for launching the app normally
    from . import myothermodule
except:
    # absolute path for launching from the editor (which causes the above to fail)
    from apps.myappname import myothermodule
```

<br/><br/><br/>

## App Icons:
> Quick note:   
> *The previous version of MicroHydra used a bizzare method of packing vectorized/polygonal icon definitions into a short string, which would be unpacked and executed by the launcher. This strategy was chosen for memory efficiency, but it felt awkward and is not used anymore. The script `polygon_to_raw_bmp.py` from the tools folder has been written to convert these old polygon defs if needed.* 

<br/>

**To put it simply:**   
MicroHydra app icons are 32x32, 1bit, raw bitmaps (not bmp files) named `icon.raw`. Your app icon should be placed in the main directory of your app, alongside the `__init__.py` file.   
You can simply create these files using the `image_to_icon.py` file in the "tools" folder.

<br/><br/>

**And, for a more thorough explanation:**

MicroHydra icons are raw, 1bit, 32x32 bitmaps.  

The built-in apps use a Python file with the bitmaps stored as constants, but this method can't be used by every because it would use too much memory.   
Instead, MH icon files contain only the byte-information of the image, so that it can be loaded directly into a MicroPython framebuffer without modification.

<br/>

I have written a script to easily create these Icons named `image_to_icon.py`.   
To use the script, make sure you have Python 3 installed on your computer, along with Pillow (a Python image editing library):
```
python3 -m pip install --upgrade pip
python3 -m pip install --upgrade Pillow
```
<br/>

After that, you can run the script using this syntax:
```
python3 path/to/image_to_icon.py path/to/your_image_file.png
```
The above example will create an `icon.raw` file in your current directory based on the image file you passed it.

The image can be any format supported by Pillow, and you can also specify other arguments to change the way your image is converted:
```
python3 path/to/image_to_icon.py --output_file path/to/output_filename.raw --invert --preview path/to/your_image_file.png
```
*(use --help to see all options)*