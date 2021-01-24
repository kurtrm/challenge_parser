// This is basic javascript code, from a very basic JS understanding, to retrieve the parse data from an Amazon S3 bucket
// I probably need to put this in a 

function buildTable(data) {
// Function that builds the basic HTML table. We let Squarespace manage the design.
	var jsonData = JSON.parse(data);  // Turn our parse data from the S3 bucket into javascript objects (JavaScript Object Notation)
	for(i=0;i<jsonData.length;i++) {
		var title = jsonData[i]["Title"];  
		var description = jsonData[i]["Description"];
		if (jsonData[i]["Parent Website"].includes("HeroX")) {
		// Reconstruct the website URL based on what the parent website key is
			var site = "https://www.herox.com" + jsonData[i]["Contest URL"];
		} else {
			var site = "https://www.challenge.gov" + jsonData[i]["Contest URL"];
		}
		 // We perform some crude HTML construction in the following variables
		var h3 = $("<h3></h3>").text(title);
		var link = $("<a></a>").attr("href", site).append(h3);
		var p = $("<p></p>").text(description);
		var creator = $("<p></p>").append($("<small></small>").append($("<i></i>").append(jsonData[i]["Creator"])));
		var awardText = jsonData[i]["Award"];
		var bAward = $("<b></b>").text("Award: ");
		var award = $("<p></p>").append(bAward).append(awardText);
		var remainingText = jsonData[i]["Days Remaining"];

		// This logic tries to get the language correct based on the time remaining for the challenge
		if (remainingText.includes("Open Until")) {
			var bRemaining = $("<b></b>").text(remainingText);
		} else {
			var bRemaining = $("<b></b>").text("Days Remaining: ").append(remainingText);
		}
		
		// This actually builds the table
		var remaining = $("<p></p>").append(bRemaining);
		if (awardText) {
			var gridItem = $("<div></div>").addClass("grid-item").append(link).append(creator).append(p).append(award).append(remaining);
		} else {
			var gridItem = $("<div></div>").addClass("grid-item").append(link).append(creator).append(p).append(remaining);
		}
		
		$(".grid-container").append(gridItem);
	};
}

// AJAX (Asynchronous Javascript and XML) request to retrieve the JSON data from the S3 bucket.
// CORS (Cross Origin Resource Sharing) rules in AWS permit our specific domains to access them.
$.ajax({
    'url' : 'https://fkhepa064l.execute-api.us-west-2.amazonaws.com/default/retrieve_parse_json',
    'type' : 'GET',
    'success' : buildTable,
    'error' : function(request,error)
    {
        console.log("Request failed.");
    }
});