import './NewsBox.css'
import { Link } from 'react-router-dom';

function NewsBox({ title, link, description }) {
    return (
        // <article> card: high-contrast white surface that lifts off the purple background
        <article className="newsBox">
            <h3 className="newsBoxTitle">{title}</h3>
            {/* description only renders when present, with comfortable line-height (set in CSS) */}
            {description && <p className="newsBoxDescription">{description}</p>}
            {/* link styled as a small, muted "source" line */}
            <Link to={link} className="newsLink">{link}</Link>
        </article>
    )
}

export default NewsBox;
