import React from 'react';
import {
  Wrench, ArrowRight, MapPin, ShieldCheck, CheckCircle2, Linkedin, Instagram,
  ThumbsUp, Camera, Users, Mail, Phone, Clock3,
} from 'lucide-react';

/* Edit your contact details here */
const CONTACT = {
  email: 'support@fixora.com',
  phone: '+91 00000 00000',
  address: 'Fixora Help Desk, Civic Centre, Your City',
  hours: 'Mon to Sat, 9:00 AM to 6:00 PM',
};

const FEATURES = [
  { icon: MapPin, title: 'Pinpoint the problem', text: 'Add a precise map location and a photo so the right team can find the issue.' },
  { icon: Wrench, title: 'Routed to the right team', text: 'Language understanding matches each report with the city department best equipped to respond.' },
  { icon: CheckCircle2, title: 'See every step', text: 'Follow progress from submission through assignment and resolution.' },
  { icon: ThumbsUp, title: 'Upvote what matters', text: 'Support issues already reported nearby so urgent problems rise to the top of the queue.' },
  { icon: Camera, title: 'Photo proof of every fix', text: 'Field workers upload a photo once the work is done, and you can see the result.' },
  { icon: Users, title: 'Teams in your own area', text: 'Officials and workers see and handle only the issues from the area they serve.' },
];

const WHY = [
  ['01', 'One report, the right department', 'Issue descriptions are analyzed to connect each report with the right city service team.'],
  ['02', 'Your location makes a difference', 'Map pins help city teams see where work is needed and understand nearby reports.'],
  ['03', 'Progress everyone can follow', 'Citizens, officials, and field workers share one clear resolution journey.'],
];

/* Styles for the new parts, scoped to the landing page */
const CSS = `
.landing .features-section .feature-grid{grid-template-columns:repeat(3,1fr);gap:18px}
.landing .features-section .feature-grid .feature-card{transition:background .2s ease,border-color .2s ease,box-shadow .2s ease,transform .2s ease}
.landing .features-section .feature-grid .feature-card:hover{background:#E6F3FA !important;border-color:#B7DCEE !important;box-shadow:0 10px 26px rgba(0,127,158,.12);transform:translateY(-3px)}
@media(max-width:950px){.landing .features-section .feature-grid{grid-template-columns:repeat(2,1fr)}}
@media(max-width:720px){.landing .features-section .feature-grid{grid-template-columns:1fr;gap:10px}}

.landing .landing-footer.big-footer{display:block;height:auto;min-height:340px;padding:60px 0 0}
.landing .big-footer .footer-grid{display:grid;grid-template-columns:1.4fr .8fr 1.4fr;gap:48px;align-items:start}
.landing .big-footer .footer-about p{margin:14px 0 20px;max-width:340px;color:var(--text-secondary);font-size:14.5px;line-height:1.7}
.landing .big-footer h4{margin:0 0 16px;font-size:15px;font-weight:700;color:var(--text)}
.landing .big-footer .footer-links{display:grid;gap:11px}
.landing .big-footer .footer-links a,.landing .big-footer .footer-links button{padding:0;border:0;background:none;text-align:left;color:var(--text-secondary);font-size:14.5px;text-decoration:none;cursor:pointer}
.landing .big-footer .footer-links a:hover,.landing .big-footer .footer-links button:hover{color:var(--primary)}
.landing .big-footer .contact-list{display:grid;gap:13px;margin:0;padding:0;list-style:none}
.landing .big-footer .contact-list li{display:flex;gap:11px;align-items:flex-start;color:var(--text-secondary);font-size:14.5px;line-height:1.5}
.landing .big-footer .contact-list svg{flex:none;margin-top:2px;color:var(--primary)}
.landing .big-footer .contact-list b{display:block;color:var(--text);font-weight:600;font-size:13px}
.landing .big-footer .footer-bottom{display:flex;justify-content:space-between;gap:12px;flex-wrap:wrap;margin-top:44px;padding:20px 0 24px;border-top:1px solid var(--border);color:var(--text-secondary);font-size:13px}
@media(max-width:950px){.landing .big-footer .footer-grid{grid-template-columns:1fr 1fr;gap:34px}.landing .big-footer .footer-about{grid-column:1/-1}}
@media(max-width:720px){.landing .landing-footer.big-footer{padding-top:40px}.landing .big-footer .footer-grid{grid-template-columns:1fr}}
`;

export default function Landing({ onAuth }) {
  return (
    <div className="landing">
      <style>{CSS}</style>

      <nav className="landing-nav wrap">
        <a className="brand landing-brand" href="#top">
          <span className="brand-mark"><Wrench /></span>
          <span>Fixora</span>
        </a>
        <div className="landing-links">
          <a href="#features">How it works</a>
          <a href="#why">Why Fixora</a>
        </div>
        <div className="nav-actions">
          <button className="button text-login" onClick={() => onAuth('login')}>Log in</button>
          <button className="button primary" onClick={() => onAuth('register')}>Get started<ArrowRight size={16} /></button>
        </div>
      </nav>

      <section className="hero wrap" id="top">
        <div className="hero-copy">
          <h1>A smart city starts<br />with <em>smart fixes.</em></h1>
          <p>Spot something that needs attention? Report it in a few steps. Fixora connects your report to the right city team and keeps you in the loop until it’s fixed.</p>
          <div className="hero-actions">
            <button className="button primary large" onClick={() => onAuth('register')}>Report an issue<ArrowRight size={18} /></button>
            <button className="button outline large" onClick={() => onAuth('login')}>Sign in to Fixora</button>
          </div>
          <div className="hero-assurance"><ShieldCheck size={16} /> Built for citizens and the city teams who serve them</div>
        </div>
        <div className="hero-art">
          <div className="art-glow" />
          <div className="city-lines">
            <div className="city-sun" />
            <div className="city-building b1" /><div className="city-building b2" />
            <div className="city-building b3" /><div className="city-building b4" />
            <div className="city-road" /><div className="road-dash" />
            <span className="art-pin pin-one"><MapPin /></span>
            <span className="art-pin pin-two"><Wrench /></span>
            <span className="art-pin pin-three"><CheckCircle2 /></span>
            <div className="art-label">
              <span className="mini-check"><CheckCircle2 size={14} /></span>
              <span><b>Issue resolved</b><small>City team updated the report</small></span>
            </div>
          </div>
          <div className="art-caption"><span className="caption-dot" /> Connected to your city</div>
        </div>
      </section>

      <section className="features-section wrap" id="features">
        <div className="section-heading">
          <span className="eyebrow">A BETTER WAY TO GET THINGS FIXED</span>
          <h2>From street-level issue<br />to city-team action.</h2>
          <p>Fixora gives residents and city departments one shared place to move local issues forward.</p>
        </div>
        <div className="feature-grid">
          {FEATURES.map((f, i) => (
            <article className="feature-card" key={f.title}>
              <span className="feature-icon"><f.icon size={21} /></span>
              <span className="feature-number">0{i + 1}</span>
              <h3>{f.title}</h3>
              <p>{f.text}</p>
            </article>
          ))}
        </div>
      </section>

      <section className="trust-strip">
        <div className="wrap trust-inner">
          <span>ONE SIMPLE PLACE TO</span>
          <b><MapPin size={16} /> REPORT</b><i />
          <b><Wrench size={16} /> ROUTE</b><i />
          <b><CheckCircle2 size={16} /> RESOLVE</b>
        </div>
      </section>

      <section className="why-section" id="why">
        <div className="wrap why-grid">
          <div>
            <span className="eyebrow">WHY FIXORA</span>
            <h2>Local problems deserve<br />a clear path to action.</h2>
            <p>Residents know their neighborhoods. City teams know how to make improvements. Fixora brings those perspectives together with clear reports, location context, and visible progress.</p>
            <button className="button primary" onClick={() => onAuth('register')}>Be part of the fix<ArrowRight size={16} /></button>
          </div>
          <div className="why-points">
            {WHY.map(([n, t, d]) => (
              <div className="why-point" key={n}>
                <span>{n}</span>
                <div><b>{t}</b><p>{d}</p></div>
                <ArrowRight size={17} />
              </div>
            ))}
          </div>
        </div>
      </section>

      <footer className="landing-footer big-footer wrap">
        <div className="footer-grid">
          <div className="footer-about">
            <a className="brand landing-brand" href="#top"><span>Fixora</span></a>
            <p>A smart city starts with smart fixes. Report local problems, reach the right city team, and follow every repair until it is done.</p>
            <div className="footer-socials" aria-label="Social media">
              <span><Linkedin size={15} />LinkedIn</span>
              <span><Instagram size={15} />Instagram</span>
            </div>
          </div>

          <div>
            <h4>Quick links</h4>
            <div className="footer-links">
              <a href="#features">How it works</a>
              <a href="#why">Why Fixora</a>
              <button onClick={() => onAuth('login')}>Log in</button>
              <button onClick={() => onAuth('register')}>Get started</button>
            </div>
          </div>

          <div>
            <h4>Contact us</h4>
            <ul className="contact-list">
              <li><Mail size={17} /><span><b>Email</b>{CONTACT.email}</span></li>
              <li><Phone size={17} /><span><b>Phone</b>{CONTACT.phone}</span></li>
              <li><MapPin size={17} /><span><b>Address</b>{CONTACT.address}</span></li>
              <li><Clock3 size={17} /><span><b>Support hours</b>{CONTACT.hours}</span></li>
            </ul>
          </div>
        </div>

        <div className="footer-bottom">
          <span>© {new Date().getFullYear()} Fixora. Civic response, made clearer.</span>
          <span>Need help? Contact your city service desk.</span>
        </div>
      </footer>
    </div>
  );
}