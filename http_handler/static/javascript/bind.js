/* To avoid closure */	
function bind(fnc, val ) {
	return function () {
		return fnc(val);
	};
}