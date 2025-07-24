export const convertDateTime = (inputTime:string) => {
    const date = new Date(inputTime);
  
    const year = date.getFullYear();
    const month = (date.getMonth() + 1).toString().padStart(2, '0');
    const day = date.getDate().toString().padStart(2, '0');
    const hour = (date.getHours() % 12 || 12).toString().padStart(2, '0');
    const minute = date.getMinutes().toString().padStart(2, '0');
    const ampm = date.getHours() < 12 ? 'AM' : 'PM';
  
    const formattedTime = `${year}/${month}/${day} ${hour}:${minute} ${ampm}`;
    return formattedTime
  }
  