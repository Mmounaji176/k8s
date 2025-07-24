import {DateRangePicker} from "@nextui-org/react";
import {parseZonedDateTime} from "@internationalized/date";
import {I18nProvider} from "@react-aria/i18n";
import { useFilterStore } from "../store/filterstore";
import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
export const TimePicker = () => {
    const {start, end} = useParams()
    const [parsedStart,setParsedStart] = useState<any>()
    const [parsedEnd,setParsedEnd] = useState<any>()
    const today = new Date();
    const day = String(today.getDate()).padStart(2, '0');
    const month = String(today.getMonth() + 1).padStart(2, '0');
    const year = today.getFullYear();
    const hours = String(today.getHours()).padStart(2, '0');
    const minutes = String(today.getMinutes()).padStart(2, '0');
    const filterStore = useFilterStore()
  
    const handlePickerChange = (value:any) => {
        const S_DD = String(value.start.day).padStart(2, '0');
        const S_MM = String(value.start.month).padStart(2, '0');
        const S_YYYY = String(value.start.year);
        const S_hh = String(value.start.hour).padStart(2, '0');
        const S_mm = String(value.start.minute).padStart(2, '0');

        const E_DD = String(value.end.day).padStart(2, '0');
        const E_MM = String(value.end.month).padStart(2, '0');
        const E_YYYY = String(value.end.year);
        const E_hh = String(value.end.hour).padStart(2, '0');
        const E_mm = String(value.end.minute).padStart(2, '0');
        
        const startDate = `${S_DD}-${S_MM}-${S_YYYY}-${S_hh}-${S_mm}`;
        const endDate = `${E_DD}-${E_MM}-${E_YYYY}-${E_hh}-${E_mm}`;
    
        filterStore.setStartDate(startDate);
        filterStore.setEndDate(endDate);
    }
    useEffect(() => {
        if (start && end && start != "1" && end != "1"){
            const startArray = start.split("-")
            const endArray = end.split("-")
            setParsedStart(`${startArray[2]}-${startArray[1]}-${startArray[0]}T${startArray[3]}:${startArray[4]}:00[Africa/Casablanca]`)
            setParsedEnd(`${endArray[2]}-${endArray[1]}-${endArray[0]}T${endArray[3]}:${endArray[4]}:00[Africa/Casablanca]`)
            filterStore.setStartDate(start);
            filterStore.setEndDate(end);
        }else{
            setParsedStart(`${year}-${month}-01T00:00:00[Africa/Casablanca]`)
            setParsedEnd(`${year}-${month}-${day}T${hours}:${minutes}:00[Africa/Casablanca]`)
            filterStore.setStartDate(`01-${month}-${year}-00-00`);
            filterStore.setEndDate(`${day}-${month}-${year}-${hours}-${minutes}`);
        }
    },[])
    return (
    <I18nProvider locale="en-Ma">
    <div className="flex w-1/2 flex-wrap md:flex-nowrap  gap-2 ">
        {
            parsedStart  &&  <DateRangePicker 
            hideTimeZone
            defaultValue={{
            start: parseZonedDateTime(`${parsedStart}`),
            end: parseZonedDateTime(`${parsedEnd}`),
            }}
            visibleMonths={2}
            onChange={(value) => handlePickerChange(value)}
            />
        }
       
    </div> 
    </I18nProvider>
    );
}
