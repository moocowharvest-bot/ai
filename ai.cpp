#include <iostream>
#include <vector>
#include <random>
#include <ctime>
#include <string>

#include <cstdio>
#include <cstdlib>
#include <cstring>

using namespace std;

#if defined(_WIN32) || defined(_WIN64)
#include <windows.h>
// Ensure we link against user32.lib for clipboard APIs (OpenClipboard etc.)
#pragma comment(lib, "user32.lib")
bool sendToClipboard(const std::string &text)
{
	if (!OpenClipboard(NULL)) return false;
	EmptyClipboard();
	size_t size = (text.size() + 1) * sizeof(char);
	HGLOBAL hMem = GlobalAlloc(GMEM_MOVEABLE, size);
	if (!hMem) { CloseClipboard(); return false; }
	void* mem = GlobalLock(hMem);
	memcpy(mem, text.c_str(), text.size() + 1);
	GlobalUnlock(hMem);
	SetClipboardData(CF_TEXT, hMem);
	CloseClipboard();
	return true;
}
#elif defined(__APPLE__)
bool sendToClipboard(const std::string &text)
{
	FILE *p = popen("pbcopy", "w");
	if (!p) return false;
	fwrite(text.c_str(), 1, text.size(), p);
	int rc = pclose(p);
	return rc == 0;
}
#else
bool sendToClipboard(const std::string &text)
{
	const char *cmds[] = {"xclip -selection clipboard", "xsel --clipboard --input", NULL};
	for (int i = 0; cmds[i]; ++i) {
		FILE *p = popen(cmds[i], "w");
		if (!p) continue;
		size_t written = fwrite(text.c_str(), 1, text.size(), p);
		int rc = pclose(p);
		if (written == text.size() && rc == 0) return true;
	}
	return false;
}
#endif

enum BodyFocus { UPPER = 0, FULL, LOWER, MAXBODY } kBodyFocusType;
std::string fondleTarget;
int kNumberOfWomen;
int kAllowBreak;
bool outdoors;
bool asleep = true;
const std::vector<std::string> color = 
	{ "darkblue ", "darkpurple ", "white ", "pink ", "dark_gray ", "burgundy ", "black ", "dark_green " };
const std::vector<std::string> maskcolor = 
	{ "darkblue ", "darkpurple ", "white ", "pink ", "black ", "dark_green " };
const std::vector<std::string> chaircolor = 
	{ "darkblue ", "darkpurple ", "white ", "pink ", "dark_gray ", "burgundy ", "black " };
const std::vector<std::string> material = 
	{ "", "lace ", "satin ", "patterned ", "transparent ", "terrycloth " };
const std::vector<std::string> mouthMaskMaterial = 
	{ "", "lace ", "patterned " };
const std::vector<std::string> outdoorFurniture = 
	{ "lounge chair", "hammock" };
const std::vector<std::string> indoorFurniture = 
	{ "bed", "couch", "massage table", "dentist chair", "comfy chair" };

int getRandomNumber(int max)
{
	std::random_device rd; // obtain a random number from hardware
	std::mt19937 gen(rd()); // seed the generator
	std::uniform_int_distribution<> distr(0, max); // define the range
  
	return distr(gen);
}

float getRandomFloat(float lo, float hi)
{
	float result = lo + static_cast <float> (rand()) /( static_cast <float> (RAND_MAX/(hi-lo)));
 
	// truncation   
	float n = std::pow(10.0f, 1); // '1' is decimal places
	result = std::round(result * n) / n ;
	
	return result;
}

std::string insertBreak()
{
	std::string result;
	
	if (kAllowBreak)
		result = "\nBREAK,\n";
	else
		result = "\n*******\n";
	
	return result;
}

std::string pickRandomString(const std::vector<std::string>& inputVector, int num = 1)
{
	std::string result;

	if (inputVector.empty())
		return result;

	for (int i = 0; i < num; i++) {
		int maxIdx = static_cast<int>(inputVector.size()) - 1;
		result += inputVector[getRandomNumber(maxIdx)];
		if (num > 1)
			result += ", ";
	}

	return result;
}

std::string getQuality()
{
	std::string result = "masterpiece, best quality, highly detailed, score_9, score_8_up, score_7_up, score_6_up, ";
	result += insertBreak();
	
	return result;
}

std::string getBody(std::string output)
{
	std::string body;

	body += "((limp body)), ";
	
	body += "((curvy body)), ";
	
	body += "breathing heavily, ";
	
	if (kBodyFocusType != UPPER || output.find("carry") != std::string::npos) {
		body += "((thick thighs:1.5)), ((thick calves)), ((short legs)), ";

		body += "((wide hips, full hips, strong legs)), ";

		if (output.find("socks") == std::string::npos)
			body += "soles of feet, woman is barefoot, ";

		if (output.find("chair") == std::string::npos && output.find("on back") == std::string::npos)
			body += "((perfect small round ass:1.3)), ";

		body += pickRandomString({
			"((spread legs)), ",
			"((crossed legs)), ",
			"",
		});
	}

	if (output.find("stomach") != std::string::npos)
		body += "perfect small breasts, ";
	else
		body += pickRandomString({"perfect voluptuous breasts, ", "one exposed perfect voluptuous breast, "});
	
	if (kBodyFocusType != LOWER) {
		body += "((thick prone limp arms:1.3)), ((short thick neck:1.3)), ";

		if (getRandomNumber(1) == 1)
			body += "wearing earrings, ";
		if (getRandomNumber(1) == 1)
			body += "wearing bracelet, ";
		if (getRandomNumber(1) == 1)
			body += "wearing necklace, ";
		if (getRandomNumber(1) == 1)
			body += "wearing ring, ";
	}
	
	if (getRandomNumber(5) == 5)
		body += "realistic perfect pale skin, ";
	else
		body += "realistic perfect tan skin, ";
	
//	if (getRandomNumber(5) == 5) {
//		body += "tattoos, ";
//	}

	body += insertBreak();
	
	return body;
}

std::string getEyes()
{
	std::string eyes;
	
	eyes += "woman has eyes closed, dark gray eye shadow, ";
	eyes += insertBreak();
		
	return eyes;
}

std::string pickUpper(std::string output)
{
	std::string upper;
	
	if (getRandomNumber(15) == 15) {
		upper += pickRandomString(color);
		upper += "cute winter hat, snow, ";
	}

	if (asleep) 
		upper += "(sleeping woman is wearing ";
	else
		upper += "(woman is wearing ";

	upper += pickRandomString(color);
	upper += pickRandomString(material);   
	if (output.find("back") != std::string::npos) {
		upper += pickRandomString({
			"low cut tank top with cleavage",
			"topless, belly button",
			"open robe, perfect breasts, no bra, chest, belly button",
			"open bathrobe, perfect breasts, no bra, chest, belly button",
			"low cut bra with cleavage",
			"full coverage bikini with cleavage",
			"open shirt, perfect breasts, no bra, chest, belly button",
			"spaghetti strap minidress with cleavage",
			"button down shirt, " + pickRandomString(color) + pickRandomString(material) + "tight skirt",
		});
	} else if (output.find("stomach") != std::string::npos) {
		upper += pickRandomString({
			"low cut tank top",
			"full coverage bikini",
			"short nightgown",
			"tight minidress",
			"slip",
		});
	} else {
		upper += pickRandomString({
			"low cut bra with cleavage",
			"full coverage bikini with cleavage",
			"low cut tank top with cleavage",
			"topless, belly button",
			"pajamas",
			"spaghetti strap minidress with cleavage",
			"slip with cleavage",
		});	   
	}
	upper += "), ";

  return upper;
}

std::string pickLower(std::string output)
{
	std::string lower;

	if (output.find("pajamas") != std::string::npos) return lower;
	
	if (asleep) 
		lower += "(sleeping woman is wearing ";
	else
		lower += "(woman is wearing ";

	lower += pickRandomString(color);
	lower += pickRandomString(material);
	if (output.find("dress") != std::string::npos || output.find("robe") != std::string::npos) {
		lower += pickRandomString({
			"cute panties",
			"panty briefs",
			"thong",
			"cheeky panties",
		});
	} else if (output.find("pajamas") == std::string::npos) {
		lower += pickRandomString({
			"cute panties",
			"panty briefs",
			"thong",
			"unzipped " + pickRandomString(color) + "jeans exposing " + pickRandomString(color) + pickRandomString(material) + "panties",
			"unzipped " + pickRandomString(color) + "pants exposing " + pickRandomString(color) + pickRandomString(material) + "panties",
			"yoga pants",
			"jeans",
			"cheeky panties",
			"socks, naked",
			"tight skirt",
		});
	}

	lower += "), ";

	return lower;
}

std::string getOutfit(std::string output)
{
	std::string outfit;
	
	if (kBodyFocusType != LOWER)
		outfit += pickUpper(output);

	if (kBodyFocusType != UPPER)
		outfit += pickLower(outfit);
		
	outfit += insertBreak();

  return outfit;
}

std::string getPose()
{
	std::string pose;
	std::vector<std::string> newPose;
	
	if (kNumberOfWomen == 2) {
		pose += "2 girls, 2 women, 2 voluptuous woman, ";
		pose += insertBreak();
	}

	pose += "(((1girl))), ";
 
//	for (int i = 0; i < kNumberOfWomen; i++) {
		
	std::string woman;
//	woman += " voluptuous";
	if (asleep) woman += " sleeping ";
//	woman += pickRandomString({"college student"});
	woman += pickRandomString({"adult woman"});
#if 0	
	if (asleep)
		newPose.push_back("(one " + woman + "), (((a blue monster cunnilingus the sleeping woman)))");
	else
		newPose.push_back("(one " + woman + "), (((a blue monster cunnilingus the woman)))");
	
	if (asleep)
		newPose.push_back("(one " + woman + "), (((a man's cock is fucking the sleeping woman's fleshy pussy)))");
	else
		newPose.push_back("(one " + woman + "), (((a man's cock is fucking the woman's fleshy pussy)))");
		
#endif

//	if (kBodyFocusType == UPPER)
//		newPose.push_back("((one " + woman + ")), (((pov of a man groping)))");

	newPose.push_back("(((floating ethereal ghost hand)))");
	
//	newPose.push_back("(((a man is massaging the sleeping woman's " + fondleTarget + ":1.5)))");

	newPose.push_back(" ");

//	if (asleep)
//		newPose.push_back("(one " + woman + "), (((a blue monster is carrying the sleeping woman)))");
//	else
//		newPose.push_back("(one " + woman + "), (((a blue monster is carrying the woman)))");

//	newPose.push_back("(((one " + woman + " restrained in air by " + pickRandomString({"red tentacles", "green vines"}) + ")))");
	
//	newPose.push_back("((one " + woman + ", red tentacles, arms held by tentacles, legs held by tentacles))");

	// put the pose in newestPose to be inserted after lying setup below
	std::string newestPose;	
	if (asleep)
		newestPose = pickRandomString(newPose);
	else
//		newestPose = "(one " + woman + "), (((a blue monster is carrying the sleeping woman)))";
		newestPose = "(((" + woman + " restrained in air by " + pickRandomString({"red tentacles", "green vines"}) + ")))";
	  
	newestPose += ", ";

	if (newestPose.find("massaging") != std::string::npos)
		pose += "((one " + woman + " is lying on a massage table";
	else if (newestPose.find("carry") == std::string::npos && newestPose.find("air") == std::string::npos) {		
		if (outdoors) {
			pose += pickRandomString({
				"((one" + woman + " is lying on a lounge chair",
				"((one" + woman + " is lying on a hammock",
			});
		} else {
			pose += pickRandomString({
				"((one" + woman + " is lying on bed",
				"((one" + woman + " is lying on couch",
				"((one" + woman + " is lying on a massage table",
				"((one" + woman + " is sitting in a dentist chair))",
				"((one" + woman + " is sitting in a comfy " + pickRandomString(chaircolor) + "chair))",
			});
		}
	}
	
	if (pose.find("lying") != std::string::npos || pose.find("curled up") != std::string::npos) {
		if (pose.find("lying") != std::string::npos) {
			if (kBodyFocusType == UPPER)
				pose += " on back";
			else if (kBodyFocusType == LOWER)
				pose += " on stomach";
			else
				pose += pickRandomString({" on back", " on stomach"});  
		}
		if (asleep)
			pose += " asleep)), ";
		else
			pose += ")), ";
	} else
		pose += ", ";

	pose += newestPose;

//	if (kBodyFocusType != LOWER) {

		if (pose.find("chair") != std::string::npos)
			pose += "((woman's head is resting on the chair)), ";
		else if (pose.find("tentacle") == std::string::npos && pose.find("massaging") == std::string::npos)
			pose += "((woman's head is resting on a pillow)), ";
				
		pose += pickRandomString({
			"(woman's head is tilted to side), ",
			"(woman's head is down), ",
		});
//	}

	pose += getEyes();
	
	std::vector<std::string> mouth;
	if (pose.find("tentacle") != std::string::npos || kBodyFocusType == UPPER) {
		if (pose.find("tentacle") != std::string::npos)
			mouth.push_back("((sleepy expression)), ((woman is snoring)), ((slimy tentacle in mouth)), ((highly detailed mouth, sexy lips, focus on mouth))");
		else
			mouth.push_back("((sleepy expression)), ((woman is snoring)), ((parted lips:1.5)), ((highly detailed mouth, sexy lips, focus on mouth))");
	}
	mouth.push_back("(((woman is wearing " + pickRandomString(maskcolor) + pickRandomString(mouthMaskMaterial) + "mouth_mask)))");

//	this might be good for the distorted far away faces
//	mouth.push_back("(((face covered:1.9))), (((mouth covered:1.9)))");

	pose += pickRandomString(mouth) + ", ";

	if (pose.find("covered") == std::string::npos) {
		if (asleep)
			pose += "((sleeping woman has a round face)), ";
		else	
			pose += "((woman has a round face)), ";
	}

	if (asleep)
		pose += "((woman is asleep)), ((woman is sleeping)), ((woman is unconscious)), ";
	else
		pose += "((woman is limp)), ((woman is relaxed)), ";
		
	pose += insertBreak();
	
	if (kNumberOfWomen == 2) {
		pose += "one voluptuous awake ";
		pose += pickRandomString({
		"American",
		"Indian",
		"Native American",
		"Slovic",
		"Samoan",
		"Hawaiian",
		"European",
		"Italian",
		"French",
		"Hispanic",
		"Nordic",
		"Pacific Islander",
		"Persian",
		"Middle Eastern"
		});
		pose += " witch standing over the college student casting and conjuring a magic spell with her hands, witch is casting a spell, witch is casting a magic spell with a magic wand creating a spell, witch's eyes are closed, ";
		pose += insertBreak();
	}
	
	return pose;
}

std::string getHair()
{
	std::string hair;
	
	hair += "((";
	hair += "long wavy ";
	if (getRandomNumber(1) == 1)
		hair += "loose ";
	std::string haircolor = pickRandomString({"blonde ", "light brown "});
	hair += haircolor;
	hair += "hair ";
	std::string hairstyle = pickRandomString({"up in a high ponytail", "half-up hairstyle"});
	hair += hairstyle;
	hair += ", floating hair strands";
	hair += ")), ";
	
	hair += insertBreak();
	
	return hair;
}

std::string getAtmosphere(std::string output)
{
	std::string atmos;
	
	std::string fullAtmos = "night scene, erotic atmosphere, tension-filled moment, lustful intensity, provocative silence, suggestive composition, partial darkness, moody tone, explicit detail, curves, taboo theme, dark, theme, warm_light, vibrant colors, soft focus, high contrast, depth of field, rich details, nature-inspired color palette, playful composition, dynamic angle, ";
	
	// Split by comma, take roughly half
	std::vector<std::string> phrases;
	size_t start = 0;
	size_t pos = 0;
	while ((pos = fullAtmos.find(", ", start)) != std::string::npos) {
		phrases.push_back(fullAtmos.substr(start, pos - start + 2)); // include ", "
		start = pos + 2;
	}
	if (start < fullAtmos.length()) {
		phrases.push_back(fullAtmos.substr(start));
	}
	
	// Randomly select roughly half
	int targetCount = phrases.size() / 2;
	std::vector<std::string> selected;
	for (int i = 0; i < targetCount && !phrases.empty(); i++) {
		int idx = getRandomNumber(phrases.size() - 1);
		selected.push_back(phrases[idx]);
		phrases.erase(phrases.begin() + idx);
	}
	
	// Concatenate selected phrases
	for (const auto& phrase : selected) {
		atmos += phrase;
	}
	
	if (outdoors) {
		atmos += pickRandomString({
			"night, ",
			"dusk, ",
		});
	}
	
	atmos += insertBreak();
	
	return atmos;
}

std::string getSetting()
{
	std::string setting;
	
	if (outdoors) {
		setting += "outdoors, ";
		
		setting += pickRandomString({
			"deck",
			"patio",
		});
		setting += ", ";

		setting += pickRandomString({
		"stars",
		"flowers",
		"hearts",
		"sunset",
		"candles",
		"incense",
		"moon",
		"forest",
		"desert",
		"lake",
		"mountains",
		"beach",
		"magic",
		"lanterns",
		"dusk",
		"night",
		"lawn",
		"waterfall",
		"rich",
		"luxurious",
		"rainbow",
		"garden",
		"cup of steaming tea",
		"umbrella",
		"empty tropical drink on small table",
	}, 3);
		
	} else {
		setting += "indoors, ";
		setting += pickRandomString({
			"spa",
			"library",
			"dungeon",
			"study",
			"living room",
			"bedroom",
			"basement",
			"hospital",
		});
		setting += ", ";

		setting += pickRandomString({
		"flowers",
		"hearts",
		"candles",
		"incense",
		"magic",
		"lanterns",
		"dusk",
		"night",
		"marble",
		"lavish",
		"stained glass",
		"curtains",
		"cross",
		"statue",
		"stars",
		"rich",
		"luxurious",
		"fireplace",
		"cup of steaming tea on small table",
	}, 3); 
		
	}
	
	setting += insertBreak();
	
	return setting;
}

std::string getShot(std::string output)
{
	std::string shot;
	std::vector<std::string> newShot;
	
	if (kNumberOfWomen == 1 && output.find("pov") == std::string::npos) {
		if (output.find("on back") != std::string::npos) {
			newShot.push_back("(close up)");
			newShot.push_back("(overhead view)");
			newShot.push_back("(high angle shot:" + to_string(getRandomFloat(1.0, 1.4)) + ")");
			newShot.push_back("(zoomed in)");
			newShot.push_back("(pov)");
			newShot.push_back("((pov from above))");
			if (output.find("massage") == std::string::npos)
				newShot.push_back("(from below)");
			if (kBodyFocusType == FULL) {
				if (output.find("socks") == std::string::npos)
					newShot.push_back("(((focus on feet, from below)))");
				newShot.push_back("(((focus on thighs)))");
			}
			if (kBodyFocusType == FULL || kBodyFocusType == UPPER) {
				newShot.push_back("(((focus on mouth)))");
				newShot.push_back("(((focus on perfect breasts)))");
			}
			newShot.push_back("(((close-up of " + fondleTarget + ")))");
			newShot.push_back("(((close-up of " + fondleTarget + ":1.3))), (((overhead view:1.3)))");
			newShot.push_back("((above view of " + fondleTarget + "))");
			newShot.push_back("(((facing viewer)))");
			newShot.push_back("(((front view)))");
			newShot.push_back("(((portrait view)))");
			newShot.push_back("(((head on view)))");
			if (asleep)
				newShot.push_back("(((view of briefs:1.3))), (sleeping woman is wearing " + pickRandomString(color) + pickRandomString(material) + " panty briefs), ((spread legs))");
			else
				newShot.push_back("(((view of briefs:1.3))), (woman is wearing " + pickRandomString(color) + pickRandomString(material) + " panty briefs), ((spread legs))");
			if (kBodyFocusType == FULL) {
				newShot.push_back("((full body))");
				newShot.push_back("(((full body:1.3))), (((far_away:1.3))), (((above view:1.3)))");
				newShot.push_back("(((far_away:1.3))), (((high angle view of crotch:1.3)))"); 
				newShot.push_back("(((full body:1.3))), (((far_away:1.3))), (((high angle shot of crotch:1.3)))");
				newShot.push_back("(((full body:1.3))), (((far_away:1.3))), (((below view of crotch:1.3)))");
				newShot.push_back("(((below view of crotch:1.3)))");
			}
		} else if (output.find("on stomach") != std::string::npos) {
			newShot.push_back("(((close-up of " + fondleTarget + ":1.3)))");
			newShot.push_back("(((ass view, above view)))");
			newShot.push_back("(((close-up of " + fondleTarget + ":1.3))), (((overhead view:1.3)))");
			newShot.push_back("((from below, rear view))");
			newShot.push_back("((low angle rear shot of " + fondleTarget + "))");
			if (output.find("massage") == std::string::npos)
			newShot.push_back("(((focus on " + fondleTarget + "))), (((rear view from below:1.5)))");
			
			if (kBodyFocusType == FULL || kBodyFocusType == LOWER) {
				newShot.push_back("(((far_away:1.3))), (((high angle view of crotch:1.3)))");
				newShot.push_back("(full body), (far_away), (high angle shot of " + fondleTarget + ")");
				newShot.push_back("(((full body:1.3))), (((far_away:1.3))), (((below view of crotch:1.3)))");
				newShot.push_back("(((below view of crotch:1.3)))");
			}
		} else if (output.find("carry") != std::string::npos) {
			newShot.push_back("((pov from above))");
			newShot.push_back("from below");
			newShot.push_back("((from below, rear view))");
			newShot.push_back("((above view of " + fondleTarget + "))");
			newShot.push_back("(((facing viewer)))");
			newShot.push_back("(((front view)))");
			newShot.push_back("(((head on view)))");
			newShot.push_back("(((side view)))");
			newShot.push_back("((low angle shot of " + fondleTarget + "))");
			if (asleep)
				newShot.push_back("(((view of briefs:1.3))), (sleeping woman is wearing " + pickRandomString(color) + pickRandomString(material) + " panty briefs), ((spread legs))");
			else
				newShot.push_back("(((view of briefs:1.3))), (woman is wearing " + pickRandomString(color) + pickRandomString(material) + " panty briefs), ((spread legs))");
			newShot.push_back("(((close-up of " + fondleTarget + ":1.3))), (((overhead view:1.3)))");
			if (kBodyFocusType == FULL || kBodyFocusType == LOWER) {
				if (output.find("socks") == std::string::npos)
					newShot.push_back("(((focus on feet, from below)))");
				newShot.push_back("(((focus on thighs)))");
			}
			if (kBodyFocusType == FULL || kBodyFocusType == UPPER) {
				newShot.push_back("(((focus on perfect breasts)))");
			}
			if (kBodyFocusType == FULL) {			
				newShot.push_back("((full body))");
				newShot.push_back("(((full body:1.3))), (((far_away:1.3))), (((above view:1.3))),");
				newShot.push_back("(((full body:1.3))), (((far_away:1.3)))");
				newShot.push_back("(((far_away:1.3))), (((high angle view of crotch:1.3)))");
				newShot.push_back("(((full body:1.3))), (((far_away:1.3))), (((below view of crotch:1.3)))");
				newShot.push_back("(((below view of crotch:1.3)))");
			}
		} else {
			newShot.push_back("(close up)");
			newShot.push_back("(overhead view)");
			newShot.push_back("(high angle shot:" + to_string(getRandomFloat(1.0, 1.4)) + ")");
			newShot.push_back("(zoomed in)");
			newShot.push_back("((above view of " + fondleTarget + "))");
			newShot.push_back("((from below, rear view))");
			newShot.push_back("(((facing viewer)))");
			newShot.push_back("(((front view)))");
			newShot.push_back("(((side view)))");
			newShot.push_back("(((head on view)))");
			newShot.push_back("((low angle shot of " + fondleTarget + "))");
			if (asleep)
				newShot.push_back("(((view of briefs:1.3))), (sleeping woman is wearing " + pickRandomString(color) + pickRandomString(material) + " panty briefs), ((spread legs))");
			else
				newShot.push_back("(((view of briefs:1.3))), (woman is wearing " + pickRandomString(color) + pickRandomString(material) + " panty briefs), ((spread legs))");
			newShot.push_back("(((close-up of " + fondleTarget + ":1.3))), (((overhead view:1.3)))");
			if (kBodyFocusType == FULL || kBodyFocusType == LOWER) {
				if (output.find("socks") == std::string::npos)
					newShot.push_back("(((focus on feet, from below)))");
				newShot.push_back("(((focus on thighs)))");
			}
			if (kBodyFocusType == FULL || kBodyFocusType == UPPER) {
				newShot.push_back("(((focus on perfect breasts)))");
			}
			if (kBodyFocusType == FULL) {			
				newShot.push_back("((full body))");
				newShot.push_back("(((full body:1.3))), (((far_away:1.3))), (((above view:1.3))),");
				newShot.push_back("(((full body:1.3))), (((far_away:1.3)))");
				newShot.push_back("(((far_away:1.3))), (((high angle view of crotch:1.3)))");
				newShot.push_back("(((focus on thighs)))");
				newShot.push_back("(((full body:1.3))), (((far_away:1.3))), (((below view of crotch:1.3)))");
				newShot.push_back("(((below view of crotch:1.3)))");
			}
			if (kBodyFocusType == FULL || kBodyFocusType == UPPER) {			newShot.push_back("(((focus on perfect breasts)))");
			}
			if (kBodyFocusType == FULL) {			
				newShot.push_back("((full body))");
				newShot.push_back("(full body), (far_away), (above view)");
				newShot.push_back("(((full body:1.3))), (((far_away:1.3)))");
				newShot.push_back("(((far_away:1.3))), (((high angle view of crotch:1.3)))");
				newShot.push_back("(((full body:1.3))), (((far_away:1.3))), (((high angle shot of " + fondleTarget + ":1.3)))");
			}
		}
	}
	
	shot += pickRandomString(newShot);
	shot += ", ";
	
	shot += insertBreak();
	
	return shot;
}

std::string getLoras()
{
	std::string lora = "<lora:SDXLHighDetail_v6-000005:1>, <lora:cindrt:1>";
	
	if (asleep && getRandomNumber(1) == 1)
		lora += ", <lora:asleep:1.7>"; 
	
	return lora;
}

int main() 
{
	std::string output;
	
	srand (static_cast <unsigned> (time(0)));

	kBodyFocusType = (BodyFocus) getRandomNumber(MAXBODY-1);
	kAllowBreak = getRandomNumber(1);
	kNumberOfWomen = 1;
 
	if (getRandomNumber(2) == 2)
		outdoors = true;   
	else
		outdoors = false;

//	if (getRandomNumber(5) == 5)
//		asleep = false;   
//	else
		asleep = true;
		
	if (kBodyFocusType == UPPER)
		fondleTarget = "breasts";
	else if (kBodyFocusType == LOWER)
		fondleTarget = pickRandomString({"perfect small round ass", "thick thighs", "soles of feet"});
	else if (kBodyFocusType == FULL)
		fondleTarget = pickRandomString({"perfect voluptuous breasts", "perfect small round ass", "thick thighs", "soles of feet"});

/*	switch (kBodyFocusType) {
		case UPPER:
			output += "UPPER, ";
			break;
		case LOWER:
			output += "LOWER, ";
			break;
		case FULL:
			output += "FULL, ";
			break;
	} */

	output += getQuality();
	output += getPose();
	output += getHair();
	output += getAtmosphere(output);
	output += getShot(output);
	output += getOutfit(output);
	output += getBody(output);
	if (kBodyFocusType == FULL || (kBodyFocusType != FULL && getRandomNumber(1) == 1))
		output += getSetting();
		
//loras are causing glitched images!
//output += getLoras();

	if (output.find("far") != std::string::npos) {
		// might need to remove face, mask and eyes closed stuff too
		output += "(((eyes covered:1.9))), (((face covered:1.9))), (((mouth covered:1.9))), ";
	}

	printf("%s", output.c_str());

	// If NO_CLIPBOARD is set in the environment, skip attempting to copy
	// from inside this process. This avoids hanging when a parent process
	// captures stdout/stderr (for example when run from a GUI wrapper).
	if (std::getenv("NO_CLIPBOARD") == nullptr) {
		if (!sendToClipboard(output))
			fprintf(stderr, "Clipboard copy failed\n");
	}

	return 0;
}
