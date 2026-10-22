// No real network, API keys, visitor data or emails are used in these tests.
import leadHandler from "./index.ts";
const origin = {"Origin":"https://mmedsystems.com","Content-Type":"application/json"};
const valid = {
  full_name:"Sample Clinician",work_email:"clinic@example.org",organization:"Example Clinic",
  job_title:"Practice Manager",country:"United States",time_zone:"Eastern Time",
  facility_type:"private_clinic",locations:"1",interests:["clinical_emr","billing"],
  timeline:"exploring",message:"Need a scheduling and billing workflow.",
  privacy_notice_accepted:true,no_phi_confirmed:true,
  website:"",turnstile_token:"mock-turnstile-token",
};
function request(body:object,headers=origin) {
  return new Request("https://example.supabase.co/functions/v1/website-lead", {
    method:"POST",headers,body:JSON.stringify(body),
  });
}
Deno.test("Cross-origin caller is blocked even with an otherwise valid submission",async()=>{
  const result=await leadHandler.fetch(request(valid,{"Origin":"https://attacker.example","Content-Type":"application/json"}));
  if(result.status!==403) throw new Error("Cross-origin request accepted");
});
Deno.test("Bad user fields and missing privacy consent are rejected",async()=>{
  const result=await leadHandler.fetch(request({...valid,privacy_notice_accepted:false}));
  if(result.status!==400) throw new Error("Invalid consent accepted");
});
Deno.test("Unknown category is rejected",async()=>{
  const result=await leadHandler.fetch(request({...valid,facility_type:"admin"}));
  if(result.status!==400) throw new Error("Unknown category accepted");
});
Deno.test("Missing server-side credentials fails closed",async()=>{
  const names=["SUPABASE_SERVICE_ROLE_KEY","RESEND_API_KEY","TURNSTILE_SECRET_KEY","LEAD_HASH_SECRET"];
  const snapshot=names.map(x=>Deno.env.get(x));
  names.forEach(x=>Deno.env.delete(x));
  try {
    const response=await leadHandler.fetch(request(valid));
    if(response.status!==503) throw new Error("Unconfigured endpoint did not fail closed");
  } finally {
    names.forEach((name,i)=>snapshot[i] ? Deno.env.set(name,snapshot[i]!) : Deno.env.delete(name));
  }
});
Deno.test("Valid inquiry is stored and notification is sent using server credentials only",async()=>{
  const names=["SUPABASE_SERVICE_ROLE_KEY","RESEND_API_KEY","TURNSTILE_SECRET_KEY","LEAD_HASH_SECRET","SUPABASE_URL"];
  const previous=names.map(x=>Deno.env.get(x));
  const beforeFetch=globalThis.fetch;
  const calls:string[]=[];
  Deno.env.set("SUPABASE_SERVICE_ROLE_KEY","testing_server_key_only");
  Deno.env.set("RESEND_API_KEY","testing_resend_key_only");
  Deno.env.set("TURNSTILE_SECRET_KEY","testing_turnstile_secret_only");
  Deno.env.set("LEAD_HASH_SECRET","testing_hash_secret_only");
  Deno.env.set("SUPABASE_URL","https://example.supabase.co");
  globalThis.fetch=async(input:Request|string|URL,init?:RequestInit)=>{
    const u=String(input);calls.push(u);
    if(u.includes("/siteverify")) return Response.json({success:true,hostname:"mmedsystems.com",action:"website_lead"});
    if(u.includes("/emails")) return Response.json({id:"sent-test-id"});
    if(u.includes("/rest/v1/website_inquiries")) {
      if(init?.method==="GET") return Response.json([]);
      if(init?.method==="POST") return Response.json([{id:"00000000-0000-4000-8000-000000000001"}]);
      if(init?.method==="PATCH") return new Response(null,{status:204});
    }
    throw new Error("Unrecognized mocked request");
  };
  try {
    const outcome=await leadHandler.fetch(request(valid));
    if(outcome.status!==200 || !(await outcome.json()).ok) throw new Error("Expected successful intake");
    if(!calls.some(x=>x.includes("/siteverify")) || !calls.some(x=>x.includes("/emails"))) {
      throw new Error("Did not verify challenge and send alert");
    }
  } finally {
    globalThis.fetch=beforeFetch;
    names.forEach((name,i)=>previous[i] ? Deno.env.set(name,previous[i]!) : Deno.env.delete(name));
  }
});
