import './NewsBox.css'
import { Link } from 'react-router-dom';
function NewsBox({title, link, description}){
    return (
        <div className="newsBox">
            <h3>{title}</h3>
            <Link to={link} className='newsLink'>{link}</Link>
        </div>
    )
}
export default NewsBox;