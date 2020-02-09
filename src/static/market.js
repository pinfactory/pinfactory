function copyElement(src, dest) {
	var tmp = document.getElementById(src).value;
	document.getElementById(dest).value = tmp;
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
	if (isNaN(value) || value <= 0) {
		el.value = "";
		return 0;
	}
	if (getNumber(id, places) == value) {
		return;
	}
	el.value = value.toFixed(places);
}

function setLabels(side) {
	if (side == "FIXED") {
		document.getElementById('funder-before-label').innerHTML = "Your payment";
		document.getElementById('fixer-before-label').innerHTML = "Funder's payment";
	} else if (side == "UNFIXED") {
		document.getElementById('funder-before-label').innerHTML = "Worker's payment";
		document.getElementById('fixer-before-label').innerHTML = "Your payment";
	} else {
		document.getElementById('funder-before-label').innerHTML = "Worker's payment";
		document.getElementById('fixer-before-label').innerHTML = "Funder's payment";
	}
	document.getElementById('funder-after-label').innerHTML = "";
	document.getElementById('fixer-after-label').innerHTML = "";
}

function copyFromTopSection() {
	setLabels(copyElement("fund-fix", "side"));
	var funderPays = getNumber("funder-pays", 0);
	var workerPays = getNumber("worker-pays", 0);
	var payout = funderPays + workerPays;
	var price = roundPlaces(workerPays/payout, 3);
	console.log("payout is " + payout);
	setNumber("quantity", payout, 0);
	if (price >= 0 && price <= 1) {
		setNumber("price", price, 3);
	}
}

function copyFromForm() {
	var side = copyElement("side", "fund-fix");
	setLabels(side);
	var maturity = getNumber("maturity", 0);
	var el = document.getElementById("maturity-" + maturity);
	if (el) {
		el.classList.add("active");
		maturitydate.value = el.title;
	} else {
		// Clear the hidden maturity
		maturitydate.value = '';
		maturity.value = 0;
	}
	var quantity = getNumber("quantity", 0);
	var price = getNumber("price", 3);
	if (quantity < 1 || price <= 0 || price > 1) {
		return;
	}

	var workerPays = Math.round(quantity * price);
	var funderPays = quantity - workerPays;

	setNumber("funder-pays", funderPays, 0);
	setNumber("worker-pays", workerPays, 0);
}

function recalculateFields(event) {
	console.log("recalculate fields called for target " + event.target.id);
	document.getElementById('submit').disabled = true;
	var invest, profit, quantity, price, fee;

	if (event.target.id.startsWith("maturity-")) {
		var maturity = document.getElementById("maturity");
		var mid = event.target.id.substr(9);
		maturity.value = mid;
		maturitydate.value = event.target.title;
		event.target.classList.add("active");
	} else if (event.target.id === "funder-pays" || event.target.id === "worker-pays" || event.target.id === "fund-fix") {
		copyFromTopSection();
	} else {
		copyFromForm();
	}
	if (maturitydate.value) {
		document.getElementById('maturity-dup-1').innerHTML = maturitydate.value;
		document.getElementById('maturity-dup-2').innerHTML = maturitydate.value;
	} else {
		document.getElementById('maturity-dup-1').innerHTML = 'the maturation date';
		document.getElementById('maturity-dup-2').innerHTML = 'the maturation date';
	}
	calculateFee();
	return;
}

function calculateFee() {
	var quantity = getNumber("quantity", 0);
	var side = document.getElementById("side").value;
	var invest;

	if (side == 'FIXED') {
	    invest = getNumber("worker-pays", 0);
	} else if (side == 'UNFIXED') {
	    invest = getNumber("funder-pays", 0);
	} else {
		document.getElementById('win-loss-explain').style.visibility = 'hidden';
		return;
	}

	if ((quantity < 1) || (invest < 1)) {
		return;
	}
	
	var profit = quantity - invest;
	var fee = Math.max(1, Math.round(profit * 0.1));
	setNumber("detail-invest", invest, 0);
	setNumber("fee", fee, 0);
	setNumber("detail-fee", fee, 0);
	setNumber("contract-payout", quantity - fee, 0)
	var submitButton = document.getElementById('submit');
	// var explain = document.getElementById('explain');
	if (getNumber("maturity", 1) < 1) {
		submitButton.disabled = true;
		return;
	} else {
		submitButton.disabled = false;
	}

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
}

function hideAdvanced() {
	document.getElementById('advanced').style.visibility = 'hidden';
	document.getElementById('hide-advanced').style.display = 'none';
	document.getElementById('show-advanced').style.display = 'inline';
	return false;
}

function showAdvanced() {
	document.getElementById('advanced').style.visibility = 'visible';
	document.getElementById('hide-advanced').style.display = 'inline';
	document.getElementById('show-advanced').style.display = 'none';
	return false;
}

function setupFields() {
	if (!document.getElementById("offerForm")) {
		return;
	}
	hideAdvanced();
	const inputs = document.querySelectorAll("a, input, select, button");
	inputs.forEach(el => {
		if (el.type === "hidden" || el.type === "submit") {
			return;
		}
		el.addEventListener("click", recalculateFields);
		el.addEventListener("input", recalculateFields);
	});

	copyFromForm();
	calculateFee();
	console.log("market.js loaded and set up");
}

if (window.top.location != window.location) {
	window.top.location = window.location;
}
window.addEventListener("load", setupFields, false);

