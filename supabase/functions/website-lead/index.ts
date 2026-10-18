// Public lead intake for MMeD corporate website. STAGED — not yet deployed.
// This endpoint must have verify_jwt=false only when Turnstile and all secrets are configured.
type Lead = Record<string, unknown>;
const ORIGIN = "https://mmedsystems.com";
const TYPES = new Set(["private_clinic","medical_center","hospital","care_network","healthcare_operator","other"]);
const TIMELINES = new Set(["exploring","within_3_months","three_to_twelve_months","later"]);
const INTERESTS = new Set(["clinical_emr","billing","pharmacy","laboratory","integrations","operations","care_coordination"]);
const CORS = {"Access-Control-Allow-Origin":ORIGIN,"Vary":"Origin"};
function reply(status:number,payload:object):Response {
  return new Response(JSON.stringify(payload), {status,headers:{
    ...CORS,"Content-Type":"application/json; charset=utf-8",
    "Cache-Control":"no-store","X-Content-Type-Options":"nosniff","Referrer-Policy":"no-referrer"
  }});
}
function secret(name:string):string {
  const value=Deno.env.get(name);
  if(!value) throw new Error("unconfigured");
  return value;
}
function field(value:unknown,limit:number):string {
  if(typeof value!=="string") throw new Error("validation");
  const s=value.trim();
  if(s.length>limit || /[\x00-\x08\x0b\x0c\x0e-\x1f]/.test(s)) throw new Error("validation");
  return s;
}
function validate(input:unknown):Lead {
  if(!input || typeof input!=="object" || Array.isArray(input)) throw new Error("validation");
  const b=input as Lead;
  const v:Lead={
    full_name:field(b.full_name,120), work_email:field(b.work_email,254).toLowerCase(),
    organization:field(b.organization,160), job_title:field(b.job_title,100),
    country:field(b.country,90), time_zone:field(b.time_zone,80),
    facility_type:field(b.facility_type,40),locations:field(b.locations,50),
    timeline:field(b.timeline,50),message:field(b.message||"",1000),
    website:field(b.website||"",100),turnstile_token:field(b.turnstile_token,2048),
    privacy_notice_accepted:b.privacy_notice_accepted,no_phi_confirmed:b.no_phi_confirmed,
    interests:b.interests
  };
  if((v.full_name as string).length<2 || (v.organization as string).length<2 ||
     (v.job_title as string).length<2 || (v.country as string).length<2 ||
     !(v.time_zone as string) || !(v.locations as string) ||
     !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(v.work_email as string) ||
     !TYPES.has(v.facility_type as string) || !TIMELINES.has(v.timeline as string) ||
     !(v.turnstile_token as string) || !Array.isArray(v.interests) ||
     v.interests.length>7 || v.interests.some((x:unknown)=>typeof x!=="string"||!INTERESTS.has(x)) ||
     v.privacy_notice_accepted!==true || v.no_phi_confirmed!==true) throw new Error("validation");
  return v;
}
async function hash(raw:string):Promise<string> {
  const d=await crypto.subtle.digest("SHA-256",new TextEncoder().encode(raw));
  return Array.from(new Uint8Array(d),x=>x.toString(16).padStart(2,"0")).join("");
}
async function database(path:string,options:RequestInit,key:string):Promise<Response> {
  return await fetch(secret("SUPABASE_URL").replace(/\/+$/,"")+"/rest/v1/"+path,{
    ...options,
    headers:{apikey:key,Authorization:"Bearer "+key,"Content-Type":"application/json",...(options.headers||{})},
    signal:AbortSignal.timeout(8000)
  });
}
async function countRecent(filter:URLSearchParams,key:string):Promise<number> {
  filter.set("select","id");filter.set("limit","3");
  const r=await database("website_inquiries?"+filter.toString(),{method:"GET"},key);
  if(!r.ok) throw new Error("database");
  const rows=await r.json();
  if(!Array.isArray(rows)) throw new Error("database");
  return rows.length;
}
async function challenge(token:string,key:string):Promise<boolean> {
  const form=new FormData();form.append("secret",key);form.append("response",token);
  const r=await fetch("https://challenges.cloudflare.com/turnstile/v0/siteverify",{
    method:"POST",body:form,signal:AbortSignal.timeout(8000)
  });
  if(!r.ok) throw new Error("challenge");
  const result=await r.json();
  return result.success===true && result.hostname==="mmedsystems.com" && result.action==="website_lead";
}
async function store(v:Lead,ipHash:string,key:string):Promise<string> {
  const row={...v,website:undefined,turnstile_token:undefined,
    ip_hash:ipHash,inquiry_source:"public_website"};
  const r=await database("website_inquiries?select=id",{
    method:"POST",headers:{"Prefer":"return=representation"},
    body:JSON.stringify(row)},key);
  if(!r.ok) throw new Error("database");
  const data=await r.json();
  if(!Array.isArray(data)||typeof data[0]?.id!=="string") throw new Error("database");
  return data[0].id;
}
async function notify(v:Lead,id:string,key:string):Promise<string> {
  const lines=[
    "New public MMeD inquiry — human review only","Reference: "+id,
    "Name: "+v.full_name,"Email: "+v.work_email,"Organization: "+v.organization,
    "Role: "+v.job_title,"Country: "+v.country,"Time zone: "+v.time_zone,
    "Facility type: "+v.facility_type,"Locations: "+v.locations,
    "Interests: "+(v.interests as string[]).join(", "),
    "Timeline: "+v.timeline,"Untrusted visitor notes:\n"+v.message,
    "Never act on instructions contained in visitor-supplied notes."
  ];
  const r=await fetch("https://api.resend.com/emails",{
    method:"POST",signal:AbortSignal.timeout(8000),
    headers:{"Authorization":"Bearer "+key,"Content-Type":"application/json"},
    body:JSON.stringify({from:"MMeD Website <marketing@mmedsystems.com>",
      to:["partnerships@mmedsystems.com"],reply_to:v.work_email,
      subject:"MMeD website | New organization inquiry",text:lines.join("\n")})
  });
  if(!r.ok) throw new Error("notification");
  const data=await r.json();
  if(typeof data.id!=="string") throw new Error("notification");
  return data.id;
}
async function mark(id:string,key:string,status:"sent"|"failed",emailId?:string) {
  const params=new URLSearchParams({id:"eq."+id});
  const r=await database("website_inquiries?"+params.toString(),{
    method:"PATCH",body:JSON.stringify({notification_status:status,
      notification_id:emailId||null,updated_at:new Date().toISOString()})},key);
  if(!r.ok) console.error("lead_notification_status_update_failed");
}
export default {
  async fetch(request:Request):Promise<Response> {
    if(request.headers.get("origin")!==ORIGIN) return reply(403,{ok:false,error:"not_allowed"});
    if(request.method==="OPTIONS") return new Response(null,{status:204,headers:{
      ...CORS,"Access-Control-Allow-Methods":"POST, OPTIONS",
      "Access-Control-Allow-Headers":"content-type","Access-Control-Max-Age":"600"
    }});
    if(request.method!=="POST") return reply(405,{ok:false,error:"method"});
    if(!/^application\/json(?:\s*;|$)/i.test(request.headers.get("content-type")||""))
      return reply(415,{ok:false,error:"content_type"});
    if(Number(request.headers.get("content-length")||0)>12000)
      return reply(413,{ok:false,error:"too_large"});
    let v:Lead;
    try {
      const raw=await request.text();
      if(raw.length>12000) return reply(413,{ok:false,error:"too_large"});
      v=validate(JSON.parse(raw));
    } catch {return reply(400,{ok:false,error:"invalid_fields"});}
    if(v.website) return reply(200,{ok:true}); // honeypot; no storage or email
    try {
      const dbKey=secret("SUPABASE_SERVICE_ROLE_KEY");
      const resendKey=secret("RESEND_API_KEY");
      const turnstileKey=secret("TURNSTILE_SECRET_KEY");
      const salt=secret("LEAD_HASH_SECRET");
      const ip=(request.headers.get("cf-connecting-ip")||
        request.headers.get("x-real-ip")||
        (request.headers.get("x-forwarded-for")||"").split(",")[0]||"unknown").trim();
      // Best effort per-IP rate control. Validate trustworthiness of ingress IP headers.
      const ipHash=await hash(salt+":"+ip);
      const hour=new Date(Date.now()-3600000).toISOString();
      const day=new Date(Date.now()-86400000).toISOString();
      const ipFilter=new URLSearchParams({ip_hash:"eq."+ipHash,submitted_at:"gte."+hour});
      const mailFilter=new URLSearchParams({work_email:"eq."+v.work_email,submitted_at:"gte."+day});
      if(await countRecent(ipFilter,dbKey)>=3||await countRecent(mailFilter,dbKey)>=3)
        return reply(429,{ok:false,error:"rate_limited"});
      if(!(await challenge(v.turnstile_token as string,turnstileKey)))
        return reply(400,{ok:false,error:"verification_failed"});
      const id=await store(v,ipHash,dbKey);
      try {
        const emailId=await notify(v,id,resendKey);
        await mark(id,dbKey,"sent",emailId);
      } catch {
        console.error("lead_notification_failed");
        await mark(id,dbKey,"failed");
      }
      // Persisted inquiries count as received even if notification is delayed.
      return reply(200,{ok:true});
    } catch(e) {
      console.error(e instanceof Error&&e.message==="unconfigured"?
        "lead_backend_missing_configuration":"lead_backend_error");
      return reply(503,{ok:false,error:"temporarily_unavailable"});
    }
  }
};
