# Colours-Generator
This program generates all colours in the 8-bit colour series

# Run
Just run the ```run.py``` and the rest it takes care.


# About
I wanted to make a program to make all the colours. So i made this using gemini. Only to realise that this is just for 8-bit colours, and not higher.

After generating 2048 shades, it automatically stops the program for 1 second and resumes. This is done in order to let the rpi cool down(since i was running this on a rpi).  

The folder structure is as follows.  
```<red value>.zip```  
And once the ```<red value>``` folders are extracted, you get  
```<red value> / <green value> / <RedValue_GreenValue_BlueValue>.png```

After every 65536 images are created - i.e. one red directory, it zips the directory and deletes the original directory. This is implemented due to disk issues on exFat filesystem, where large number of files will cause the disk to show that no space is left.
