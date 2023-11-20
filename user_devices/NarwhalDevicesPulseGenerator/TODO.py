ON FPGA:

DONE:Fix "current address"

Add wait monitor
    - Increase width size of notification FIFO - check that you still meet timing
    - Need to have fixed "current address problem". Actually, I probably dont.?
    - figure out how wait monitor needs to work. Something like: if last instructin has wait tag, add current global time time to notification queue.


On labsctipt driver:

Figure out why sometimes crashes when computer sleeps

Add wait monitor








state_pipeline.d -> 
129 - from state_save.q
320 - from instr_state

state_save.d ->
154 - from static state - IGNORE
320 - from instr_state (same as above)

So it is really only:

129: 
state_pipeline.d = state_save.q;

320:
state_pipeline.d = instr_state;
state_save.d = instr_state;



ram.addrb = 
142:
346:
352:
356: