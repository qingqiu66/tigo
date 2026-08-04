var requestId = crypto.randomUUID();
var iccid = process.argv[2];
console.log('ICCID: %o', iccid);
var authData = await api(`/get-simcard?serialNumber=${iccid}&requestId=${requestId}&type=chip`);
// console.log(authData);
var orderInfo = {
  "customer":{
    "first_name":"Carmen","second_name":"Elizabeth",
    "surname":"Mejía","second_surname":"",
    "dob":"1991-09-05",
    "identification":"045198327",
    "identification_type":"DUI",
    "gender":null,"identification_issue_date":null,"identification_exp_date":null,"email":null,"contact_phone_number":null,
    "address":{"state":"SANTA ANA","city":"SANTA ANA"},"nationality":null,"manual_input":false},
  "activation":[
    {"offer":{},"offer_device":{},"resources":[
      {"parameters":[
        {"name":"model"},{"name":"imei"},
        {"name":"icc","value":iccid},
        {"name":"msisdn","value":authData.msisdn.value},
        {"name":"request_id","value":requestId}]}]}],
  "order":{"reference_number":"","date":"","action":"PREPAID_ACTIVATION","journey":"activation"}};
var order = await api('/activation/order', {
  method: 'POST',
  headers: {
    'content-type': 'application/json',
    'authorization': `Bearer ${authData.accessToken.value}`
  },
  body: JSON.stringify(orderInfo)
});
console.log(JSON.stringify(order));
console.log('msisdn: %o',order.activation.attributes.resources.attributes.parameters.attributes.msisdn.value)

async function api(url, opts={}) {
  if (!opts.headers) opts.headers = {};
  opts.headers.referer = "https://activate.tigo.com.sv/";
  var req = await fetch('https://activate-sv-xapis-prod.tigocloud.net/sv'+url,opts);
  var res = await req.json();
  // console.log(res)
  var {result,data} = res.response;
  if (result.code !== 200) {
    console.log('authError:',result)
    throw new Error(result.result_message.value);
  }
  return data;
}
