function getURLParameter(name) {
	return decodeURI(
		(RegExp(name + '=' + '(.+?)(&|$)').exec(location.search)||[,null])[1]
	);
}

function removeItem(item, array) {
	array.splice($.inArray(item, array), 1);
}