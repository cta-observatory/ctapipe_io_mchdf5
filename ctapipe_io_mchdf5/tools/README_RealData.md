Workflow for real data
======================

-  Not at all in the ideal way, although it will rest as it is, otherwise it will probably change 
the way it should be done 

! Run the scripts in the order they are ordered.

1. Within the `dl0_manual_calib` BRANCH, the first script turns once (yeap... going all through the source file, computing the 
manual calibration and applying it), to compute the number of pixels within the cleaning method. If  this number is 
large (>1750), then the i_event is classified as a FLAT FLIED. The corresponding number of the events are saved into a 
dictionary and later saved within a pickle.

    1.1. The problem of this file was that the run did not have correctly triggered these events.
    
2. Turn to the `master` branch and run the second script. It will look into the pickle to see whether an i_event 
corresponds to a flat event or not, and will only convert the NO flat flied to and hdf5 file. 

3. Run the last script, returning to the `dl0` branch, to run the original code only in the images that we are 
interested in. Offline calibration (Franca's method) and the zero suppression (Konrad & Lenkas' method) will be applied,
computing the size of the corresponding file.
    
    3.1 CHECK that the channel_selection (just keeping HI or LO or a mix of both) is implemented within the chain. 
    


