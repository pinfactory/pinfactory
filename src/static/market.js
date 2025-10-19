function copyElement(src, dest) {
  srcElement = document.getElementById(src);
  destElement = document.getElementById(dest);
  var tmp = document.getElementById(src).value;
  if (srcElement && destElement) {
    if (destElement.hasOwnProperty('value')) {
      destElement.value = srcElement.value;
    } else {
      destElement.innerHTML = srcElement.value;
    }
  }

	return tmp;
}

function roundPlaces(n, decimals) {
	return Number(Math.round(n+'e'+decimals)+'e-'+decimals);
}

function getNumber(id, places) {
	const el = document.getElementById(id);
	if (!el) {
		console.log("No element for " + id);
		return 0;
	}
	var x = parseFloat(el.value);
	if (isNaN(x)) {
		return 0;
	}
	x = Math.round(x * 10 ** places) / (10 ** places)
	if (x < 0) {
		return 0;
	}
	return x - 0;
}

function setNumber(id, value, places) {
	const el = document.getElementById(id);
	if (!el) {
		console.log("can't find element " + id)
		return 0;
	}
	if (!el.hasOwnProperty('value')) {
    el.innerHTML = value;
    return;
	}
	if (isNaN(value) || value <= 0) {
		el.value = "";
		return 0;
	}
	if (getNumber(id, places) == value) {
		return;
	}
	el.value = value.toFixed(places);
}

function recalculateFields(event) {
	console.log("recalculate fields called for target " + event.target.id);
  doRecalculate();
}

function doRecalculate() {
  console.log("doRecalculate called");
	var quantity = getNumber("quantity", 0);
	var price = getNumber("price", 3);
	var side = document.getElementById("side").value;
	var invest = quantity * price;
	var profit = quantity - invest;
	var fee = Math.max(1, Math.round(profit * 0.1));
	setNumber("detail-invest", invest, 0);
	setNumber("detail-fee", fee, 0);
	setNumber("contract-payout", quantity - fee, 0)
	var otherSideText = 'resolved as a loss';
	var thisSideText = 'resolved as a win';
	if (side == 'FIXED') {
		thisSideText = 'FIXED';
		otherSideText = 'UNFIXED';
	} else if (side == 'UNFIXED') {
		thisSideText = 'UNFIXED';
		otherSideText = 'FIXED';
	}
	document.getElementById('this-side-dup').innerHTML = thisSideText;
	document.getElementById('other-side-dup').innerHTML = otherSideText;
	document.getElementById('win-loss-explain').style.visibility = 'visible';
	el = document.getElementById("cmd-side");
	el.innerHTML = side;
  setNumber("cmd-price", price, 0);
  setNumber("cmd-quantity", quantity, 0);
  var mid = document.getElementById("maturity").value;
  setNumber("cmd-mid", mid, 0);
}

function setupFields() {
	if (!document.getElementById("offerForm")) {
		return;
	}
	const inputs = document.querySelectorAll("a, input, select, button");
	inputs.forEach(el => {
		if (el.type === "hidden" || el.type === "submit") {
			return;
		}
		el.addEventListener("click", recalculateFields);
		el.addEventListener("input", recalculateFields);
	});
	doRecalculate();
	console.log("market.js loaded and set up");
}

if (window.top.location != window.location) {
	window.top.location = window.location;
}
window.addEventListener("load", setupFields, false);
