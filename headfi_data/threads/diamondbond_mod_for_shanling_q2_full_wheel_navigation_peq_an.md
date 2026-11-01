# DiamondBond mod for Shanling Q2 - Full Wheel Navigation, PEQ and more!

- **Forum Section**: Portable Source Gear
- **Original Author**: Shanling
- **Total Replies / Views**: 130 / 5K
- **Thread URL**: [https://www.head-fi.org/threads/diamondbond-mod-for-shanling-q2-full-wheel-navigation-peq-and-more.981537/unread](https://www.head-fi.org/threads/diamondbond-mod-for-shanling-q2-full-wheel-navigation-peq-and-more.981537/unread)

## Attached Gear Images

![Attached Image](../images/th_diamondbond_mod_for_shanling_q2_full_wheel_navigation_peq_an_img_32140.jpg)

## Discussion Posts & Comments

### Post #1 by **Member** ()

I'll try the new one, I went back to stock 1.01 because battery seemed to be dropping faster. But it could be that I was messing with it more. Got to try minimal too

---

### Post #2 by **Member** ()

abitdeef said:

			I'll try the new one, I went back to stock 1.01 because battery seemed to be dropping faster. But it could be that I was messing with it more. Got to try minimal too
		
Click to expand...
Few people in our discord are saying the new releases have improved their battery
hard to tell what's going on, I think user differences and differing usage styles will make a huge difference of course, but have you tried low power mode?

---

### Post #3 by **Member** ()

diamondbond said:

			Ahhh, in 1.0.6 there is still the option to adjust the scrolling speed, but after tests from various people and myself, we determined 50% was the right speed to retain control and not overscroll/overshoot so we removed the wheel sensitivity option all-together to remove confusion for users - and it can still be quite fast as there is acceleration, anyway enjoy the night! Let me know how the latest iPod build is tomorrow
Click to expand...

Interesting, I have been running mine set at 130%.
diamondbond said:

			Few people in our discord are saying the new releases have improved their battery
hard to tell what's going on, I think user differences and differing usage styles will make a huge difference of course, but have you tried low power mode?
		
Click to expand...

From years working on this position, I can tell you that nothing in world is more confusing than customer feedback.

Just wait until they start discussion which of your firmware versions sounds the best

---

### Post #4 by **Member** ()

diamondbond said:

			Few people in our discord are saying the new releases have improved their battery
hard to tell what's going on, I think user differences and differing usage styles will make a huge difference of course, but have you tried low power mode?
		
Click to expand...

No I've not tried low power mode, but I updated to the latest ipod version and it seems to be normal now. I was comparing different headphones so the screen might have been on more.... but it did seem like it was draining faster just in standby. All is well and hey I'm just reporting what I'm experiencing ATM. You know I'm very happy with the mod. Love all the improvements.

To be fair there are instances where firmware can affect the sound. But no, I've noticed no changes there 
 Sound character is a rabbit hole itself. I personally think this setup sounds better than the m1 plus , of course the m1 plus has more power, but Q2 has plenty for me. Honestly I'll say it again, I couldn't be happier- with my hearing a peq helps because of more boost and control and that's the thing I wanted most besides more wheel implementation. And we got both in spades.

---

### Post #5 by **Member** ()

I've purchased a Q2 after seeing what this modded firmware is able to do! I am very excited to see how it improves in the future!

---

### Post #6 by **Member** ()

Shanling said:
			
		

			Interesting, I have been running mine set at 130%.
		
Click to expand...

130% is crazy! 
 I guess that proves how subjective the wheel speed is too, I thought 50% was already on the edge of becoming difficult to control once the acceleration kicks in.

I will add back the wheel sensitivity option seeing as how the wheel speed varies between devices.

			
				Shanling said:
			
		

			From years working on this position, I can tell you that nothing in world is more confusing than customer feedback.

Just wait until they start discussion which of your firmware versions sounds the best 
Click to expand...

Yep I'm quickly learning what you mean about customer feedback lol, especially with battery life where everyone's usage is so different!

			
				abitdeef said:
			
		

			No I've not tried low power mode, but I updated to the latest ipod version and it seems to be normal now. I was comparing different headphones so the screen might have been on more.... but it did seem like it was draining faster just in standby. All is well and hey I'm just reporting what I'm experiencing ATM. You know I'm very happy with the mod. Love all the improvements.
		
Click to expand...

I've improved it a bit more now by reducing the UI loop wakes when the device is idle (coming in 1.1.5). Interestingly I only just properly learned what the auto-standby function implemented by Shanling engineers does on the Q2 firmware; it actually enables Linux's native `suspend` functionality. I had assumed it was more of a normal software standby before digging into it.

			
				abitdeef said:
			
		

			To be fair there are instances where firmware can affect the sound. But no, I've noticed no changes there 
 Sound character is a rabbit hole itself. I personally think this setup sounds better than the m1 plus , of course the m1 plus has more power, but Q2 has plenty for me. Honestly I'll say it again, I couldn't be happier- with my hearing a peq helps because of more boost and control and that's the thing I wanted most besides more wheel implementation. And we got both in spades.
		
Click to expand...

PEQ was probably one of my favourite parts of Q2 Pod too, because the Q2 already has more than enough power for a lot of IEMs/headphones and all I was left desiring was proper wheel navigation and PEQ would have been the cherry on top of that, I'm so glad I was able to bring those desires to life.

			
				Carbon44 said:
			
		

			I've purchased a Q2 after seeing what this modded firmware is able to do! I am very excited to see how it improves in the future!
		
Click to expand...

So glad to hear that, honestly seeing people actually buying a Q2 specifically because of this mod is still slightly surreal 
 I hope you enjoy your Q2 when it arrives!

---

### Post #7 by **Member** ()

Hey everyone,

I'm considering upgrading to the Shanling Q2 for my 20th birthday at the end of the month. I've been using a HiBy M300 (4GB/128GB) for over a year, but after dropping streaming to focus purely on local CD rips and FLAC files, I'm really drawn to the pure-audio workflow and retro click-wheel UI that DiamondBond's q2-pod firmware brings to the Q2.

Before buying, I had a few technical questions for Q2 owners and developers running q2-pod:
USB-C Headphone Handshake (Sennheiser Momentum 4):
Has anyone tested active USB-C headphones like the Momentum 4 directly over the Q2's USB digital output? Does the MTouch/Linux stack handshake properly as a host, or does it strictly expect standard external DAC dongles? 
(If not, I can fall back to LDAC Bluetooth when out and about).
Wake-up Pops & Relay Muting:
On my M300 (using Poweramp Direct Hi-Res), I regularly get annoying power-on/wake-up pops when resuming playback as the single CS43131 energizes. How does the Quad CS43131 implementation on the Q2 handle this? Is the noise floor completely black during pause/play transitions and sample-rate changes?
Lyrics Support in q2-pod:
How does q2-pod handle synced .lrc files and embedded metadata tags? Is toggling over to the lyrics view on the Now Playing screen seamless via the touch wheel?
Library Navigation Speed & Indexing:
For those with 100GB+ SD cards, how snappy is list scrolling and index scanning compared to Android DAPs? Does the touch-wheel velocity acceleration feel responsive across large artist/album lists?
Real-World Battery Life:
How is battery drain holding up when running q2-pod over 3.5mm high gain vs Bluetooth output?
Huge thanks to DiamondBond and everyone contributing to this firmware project—it looks like an incredible piece of software! Appreciate any insights.

---

### Post #8 by **Member** ()

No wake up pops, I use hi gain and peq and get 10 to 11 hours depending on how much I fiddle with it. Bluetooth is longer, haven't got exact number but maybe 18 hours?? Someone else can give you a better idea I'm sure but it's more than 3.5 out.

---

### Post #9 by **Member** ()

Hey everyone,

I'm considering upgrading to the Shanling Q2 for my 20th birthday at the end of the month. I've been using a HiBy M300 (4GB/128GB) for over a year, but after dropping streaming to focus purely on local CD rips and FLAC files, I'm really drawn to the pure-audio workflow and retro click-wheel UI that DiamondBond's q2-pod firmware brings to the Q2.
		
Click to expand...

Happy early birthday! Honestly your use case is very similar to mine, I think you will like the Q2 quite a bit.

For your questions:

1. 
USB-C headphones / Momentum 4:
 I haven't personally tested the Momentum 4 over USB-C, so I don't want to tell you it works when I haven't verified it. The Q2 does have USB digital output, but whether active USB-C headphones enumerate correctly versus a normal USB DAC depends on how Shanling's MTouch/Linux USB audio implementation handles the device. If anyone here has a pair I'd be interested in the result too. LDAC is obviously the safe fallback.

2. 
Wake-up pops:
 I've never noticed any obvious pops on my Q2 during normal pause/resume use, and the analogue output is very quiet to me. I'd still like other owners to chime in though, since I mostly use IEMs and haven't specifically tested every sample-rate transition. Q2 Pod doesn't replace the low-level DAC handling, so this is still largely Shanling's implementation.

3. 
Lyrics:
 Lyrics are something I'm still working on. The Now Playing UI and wheel navigation are heavily modified by Q2 Pod, but I don't want to overpromise `.lrc` or embedded lyrics support until that side is finished properly.

4. 
Library speed:
 This is one of the areas I'm quite happy with now. Wheel scrolling has acceleration, so spinning faster moves through long lists faster, and menus remember your previous position. Navigation feels very fast once the library has been scanned. Initial indexing is still handled by the Q2's local music scanner, so with 100GB+ the scan time will depend more on file count and SD card speed than capacity alone.

5. 
Battery:
 This is difficult to give a single number for because everyone's usage is different but 
@abitdeef
 has some nice estimates!  also I've recently reduced unnecessary UI loop wakeups while the device is idle (Q2 Pod also has a low power mode and optional 80% charge limit). I don't have a controlled high-gain vs Bluetooth runtime comparison yet though I feel like the Bluetooth one would win out by a fair margin as the DAC's are powered down during that scenario I believe.

Also, Q2 Pod is built on top of Shanling's stock firmware rather than replacing the OS. Things like the DAC drivers, USB stack and a lot of the lower-level audio and power behavior are still Shanling's original implementation.

If you're moving away from streaming and mainly want something small for local music, I think the Q2 fits that use case very well.

btw 
@Shanling
 I see why you use 130% now, its crazy fast & precise, I can go through 400+ item list rows and end exactly where I want to.

1.1.5 is out with some slight Battery runtime improvements and Wheel sensitivity added back into Settings, but this time it is done nicely with a proper fancy wheel scroll to adjust the sensitivity itself.

Also we have a User Guide now that is inspired by Apple's User Guide's from the iPod Classic, you can download it from the Releases page.

---

### Post #10 by **Member** ()

Yes I forgot happy B day and welcome. I'm old so B days are just another year towards the end at this point lol

---

### Post #11 by **Member** ()

Hello! 

My Q2 has arrived sooner than expected. I got to use it a bit today. Here are some of my thoughts on it using the Q2-Pod firmware! 

It is likely that Q2's stock OS would have been a deal breaker for me... 
Here's what I have utilized already on the Q2-Pod firmware:

PEQ Preamp:
 I set it to -12dB for 
much better
 volume granularity on my 
extremely
 sensitive Campfire Audio Clara. Stock would have me stuck at 3-4 volume, with no room in between to get to the level I want, even on low gain/3.5mm. I was very worried a slight touch of the touch wheel would send the volume way up to dangerous levels. 
Maximum volume setting:
 Similar to the above. I nearly deafened myself already, fiddling around with the stock OS. This safety feature is appreciated. (Apologies if this is a stock MTouch feature I missed, I did not stay long because of the volume issue) 
Better navigation:
 Duh, scrolling on such a small touch screen is a little silly unless you need very fine, or very extreme scrolls. 
Themes/Style:
 I've had a Shanling M0 Pro in the past. MTouch is 
fine
. It works. But a little customization goes a long way. Coverflow is a nice way of navigating my music library. 

It is a sweet little device. In this state, I prefer it to my Hiby M300 as well as my A&K SP3000M. I have been saying for years there's no reason why we can't have a modern iPod Nano, with how much technology has advanced since. Well this is the closest we've gotten and I am all for it.

---

### Post #12 by **Member** ()

Larger album art in now playing in ipod UI. Must download..... 
 Diamond, you the man!!!

---

